#coding: utf-8
'''
# Installation

`pip install` dependencies:
  * `trio`
  * `asks`
  * `contextvars` (before Python 3.7)
  
Overlay view dependencies:
  * overlay
  * gestures
'''

# Trio workarounds for Pythonista, see https://github.com/python-trio/trio/issues/684
import warnings, signal
with warnings.catch_warnings():
  warnings.simplefilter("ignore")
  import trio
import asks
asks.init('trio')
signal.signal(signal.SIGINT, signal.SIG_DFL)
#trio._core._run._MAX_TIMEOUT = 1.0

import functools, types, inspect, time

from overlay import Overlay, AppWindows
import ui, objc_util


class ValueNotDefinedYet(Exception):
  
  def __init__(self):
    super().__init__('Value has not been returned yet. Did you forget to yield?')


class GeneratorValueWrapper():
  
  def __init__(self, gen):
    self.gen = gen
    self._value = ValueNotDefinedYet()
    
  @property
  def value(self):
    if isinstance(self._value, Exception):
      raise Exception(str(self._value)) from self._value
    else:
      return self._value
    
  def cancel(self):
    trio._scripter.cancel(self)


def script(func):
  '''
  Decorator for the async scripts.
  
  Scripts piggyback on the trio event loop.
  
  Script actions execute in parallel until the next `yield` statement.
  
  New scripts suspend the execution of the parent script until all the parallel scripts have
  completed, after which parent script execution is resumed.
  '''
  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    scr = trio._scripter
    if inspect.isgeneratorfunction(func):
      gen = func(*args, **kwargs)
    elif inspect.iscoroutinefunction(func):
      gen = func(*args, **kwargs)
      gen = scr._async_handler(gen)
      return gen
    else:
      def gen_wrapper(func, *args, **kwargs):
        func(*args, **kwargs)
        yield
      gen = gen_wrapper(func, *args, **kwargs)
    scr.parent_gens[gen] = scr.current_gen
    if scr.current_gen != 'root':
      scr.standby_gens.setdefault(scr.current_gen, set())
      scr.standby_gens[scr.current_gen].add(gen)
      scr.deactivate.add(scr.current_gen)
    scr.activate.add(gen)

    scr.wake_up.set()
    
    value_wrapper = GeneratorValueWrapper(gen)
    scr.value_by_gen[gen] = value_wrapper

    return value_wrapper
    
  return wrapper
  
'''
def extract(gen):
  "Extracts the returned value of a completed script. Raises an Exception if the value is not available."
  #loop = asyncio.get_event_loop()
  #scr = loop._scripter
  scr = trio._scripter
  try:
    value = scr.value_by_gen[gen]
  except KeyError:
    raise Exception('No value available. Remember to return a value from the script and yield before calling extract. ')
  if isinstance(value, Exception):
    raise Exception('Task raised an exception:' + str(value.args)) from value
  else:
    return value
'''
  
  
class Scripter():
  
  default_duration = 0.5
  
  def __init__(self):
    self.cancel_all()
    #loop = asyncio.get_event_loop()
    #self._session = aiohttp.ClientSession(loop=loop)
    
  def end_all(self):
    if not self._session.closed:
      self._session.close()
  
  async def update(self, nursery):
    '''
    Main Scripter animation loop handler, called by the Puthonista UI loop and never by your
    code directly.
    
    This method:
      
    * Activates all newly called scripts and suspends their parents.
    * Calls all active scripts, which will run to their next `yield` or until completion.
    * As a convenience feature, if a `yield` returns `'wait'` or a specific duration,
    kicks off a child `timer` script to wait for that period of time.
    * Cleans out completed scripts.
    * Resumes parent scripts whose children have all completed.
    * Sets `update_interval` to 0 if all scripts have completed.
    '''
    run_at_least_once = True
    while run_at_least_once or len(self.activate) > 0 or len(self.deactivate) > 0:
      run_at_least_once = False
      for gen in self.activate:
        self.active_gens.add(gen)
      for gen in self.deactivate:
        self.active_gens.remove(gen)
      self.activate = set()
      self.deactivate = set()
      gen_to_end = []
      for gen in self.active_gens:
        self.current_gen = gen
        wait_time = self.should_wait.pop(gen, None)
        if wait_time is not None:
          timer(wait_time)
        else:
          yielded = None
          try:
            yielded = next(gen)
          except StopIteration as stopped:
            if gen not in self.deactivate:
              gen_to_end.append(gen)
            self.value_by_gen[gen]._value = stopped.value
            del self.value_by_gen[gen]
          if yielded is not None:
            if yielded == 'wait':
              yielded = self.default_duration
            if type(yielded) in [int, float]:
              self.should_wait[gen] = yielded
            elif type(yielded) is tuple:
              coro, queue = yielded
              async def async_runner(coro, queue):
                try:
                  value = await coro
                  queue.put_nowait(value)
                except Exception as e:
                  queue.put_nowait(e)
              nursery.start_soon(async_runner, coro, queue)
      self.current_gen = 'root'
      self.time_paused = 0
      for gen in gen_to_end:
        self.active_gens.remove(gen)
        parent_gen = self.parent_gens[gen]
        del self.parent_gens[gen]
        if parent_gen != 'root':
          self.standby_gens[parent_gen].remove(gen)
          if len(self.standby_gens[parent_gen]) == 0:
            self.activate.add(parent_gen)
            del self.standby_gens[parent_gen]
    return len(self.active_gens) + len(self.standby_gens) > 0
    #  self.update_interval = 0.0
    #  self.running = False
      
  def cancel(self, script):
    ''' Cancels any ongoing animations and
    sub-scripts for the given script. '''
    to_cancel = set()
    to_cancel.add(script)
    parent_gen = self.parent_gens[script]
    if parent_gen != 'root':
      self.standby_gens[parent_gen].remove(script)
      if len(self.standby_gens[parent_gen]) == 0:
        self.active_gens.add(parent_gen)
        del self.standby_gens[parent_gen]
    found_new = True
    while found_new:
      new_found = set()
      found_new = False
      for gen in to_cancel:
        if gen in self.standby_gens:
          for child_gen in self.standby_gens[gen]:
            if child_gen not in to_cancel: 
              new_found.add(child_gen)
              found_new = True
      for gen in new_found:
        to_cancel.add(gen)

    for gen in to_cancel:
      if gen == self.current_gen:
        self.current_gen = parent_gen
      del self.value_by_gen[gen]
      del self.parent_gens[gen]
      self.activate.discard(gen)
      self.deactivate.discard(gen)
      self.active_gens.discard(gen)
      if gen in self.standby_gens:
        del self.standby_gens[gen]
      
  def cancel_all(self):
    ''' Initializes all internal structures.
    Used at start and to cancel all running scripts.
    '''
    self.current_gen = 'root'
    self.should_wait = {}
    self.parent_gens = {}
    self.value_by_gen = {}
    self.active_gens = set()
    self.standby_gens = {}
    self.activate = set()
    self.deactivate = set()
    #self.running = False
  
  @script
  def _async_handler(self, coro):
    queue = trio.Queue(1)
    yield (coro, queue)
    while True:
      try:
        return queue.get_nowait()
      except trio.WouldBlock:
        pass
      yield 
  
  async def _scripter_runner(self, nursery):
    while True:
      if not await self.update(nursery):
        if not self.forever: break
        with trio.move_on_after(1):
          await self.wake_up.wait()
          self.wake_up.clear()
      await trio.sleep(0)
  
  async def _runner(self):
    #loop = asyncio.get_event_loop()
    #i = 0
    if self.start_script:
      self.start_script()
    async with trio.open_nursery() as nursery:
      if self.hud:
        self.overlay = self.open_overlay()
      nursery.start_soon(self._scripter_runner, nursery)
    print('end')
    #self.end_all()
    
  def close_down(self):
    task = trio.hazmat.current_root_task()
    print(dir(task))

  @objc_util.on_main_thread
  def open_overlay(self):
    view = ui.View(name='Trio')
    view.frame = (0, 0, 200, 1)
    view.flex = 'WH'
    view.background_color = 'white'
    o = Overlay(content=view, parent=AppWindows.root())
    o.close_callback = self.close_down
    return o

  @classmethod
  def run(cls, start_script=None, forever=False, hud=False):
    print('starting')
    trio._scripter = scr = Scripter()
    scr.forever = forever
    scr.hud = hud
    scr.start_script = start_script
    scr.wake_up = trio.Event()
    trio.run(scr._runner)
    print('done')

  @classmethod
  def bootstrap(cls):
    scr = Scripter()
    loop = asyncio.get_event_loop()
    loop._scripter = scr
    print('starting')
    loop.call_soon(scr._runner())
    print('done')

@script
def timer(duration=None, action=None):
  ''' Acts as a wait timer for the given 
  duration in seconds. Optional action 
  function is called every cycle. '''  
  duration = duration or 0.3
  start_time = time.time()
  dt = 0
  while dt < duration:
    if action: action()
    yield
    dt = time.time() - start_time

@script
async def get(*args, **kwargs):
  response = await asks.get(*args, **kwargs)
  return response
  
@script
async def post(*args, **kwargs):
  response = await asks.post(*args, **kwargs)
  return response
  

if __name__ == '__main__':

  sites = '''youtube.com
facebook.com
baidu.com
wikipedia.org
reddit.com
yahoo.com
google.co.in
amazon.com
twitter.com
sohu.com
instagram.com
vk.com
jd.com
sina.com.cn
weibo.com
yandex.ru
google.co.jp
google.co.uk
list.tmall.com
google.ru
google.com.br
netflix.com
google.de
google.com.hk
twitch.tv
google.fr
linkedin.com
yahoo.co.jp
t.co
microsoft.com
bing.com
office.com
xvideos.com
google.it
google.ca
mail.ru
ok.ru
google.es
pages.tmall.com
msn.com
google.com.tr
google.com.au
whatsapp.com
spotify.com
google.pl
google.co.id
xhamster.com
google.com.ar
xnxx.com
google.co.th
Naver.com
sogou.com
accuweather.com
goo.gl
sm.cn
googleweblight.com'''.splitlines()

  import datetime

  s = asks.Session(connections=100)

  async def grabber(site):
    r = await s.get('https://'+site, timeout=5)
    content = r.text
    #print(site)

  async def main():
    async with trio.open_nursery() as n:
      for site in sites:
        n.start_soon(grabber, site)

  @script
  def retrieve_all():
    for site in sites:
      worker(site)
    print(site)

  @script
  def worker(site):
    result = get('https://'+site, timeout=5)
    yield
    content = result.value.text
    

  def baseline_requests():
    import requests
    for site in sites:
      print(site)
      url = 'https://'+site
      try:
        resp = requests.get(url, timeout=(5,5))
        content = resp.text
      except Exception as e:
        print(str(e))

  @script
  def simple_test():
    print('hello')
    #yield # inserted automatically

  start = datetime.datetime.now()
  
  #baseline_requests()
  #trio.run(main)
  #Scripter.run(lean_retriever)
  Scripter.run(simple_test, forever=True, hud=True)
  
  duration = datetime.datetime.now() - start
  print(len(sites), 'sites in', str(duration))