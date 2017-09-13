#coding: utf-8
from ui import *
from types import GeneratorType
from numbers import Number
from functools import partial
import time, math

'''
Features:
  
  + Inherits ui.View, enable by inheriting
  + Or 
'''

SLOW = 0
FAST = 1
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def script(func):
  ''' Decorator for the stepper functions. '''
  def wrapper(self, *args, **kwargs):
    gen = func(self, *args, **kwargs)
    if not isinstance(gen, GeneratorType):
      return gen
    self.parent_gens[gen] = self.current_gen
    if self.current_gen != 'root':
      self.standby_gens.setdefault(self.current_gen, set())
      self.standby_gens[self.current_gen].add(gen)
      self.deactivate.add(self.current_gen)
    self.activate.add(gen)
    self.update_interval = self.default_update_interval

    return gen
    
  return wrapper
 

class ScriptedBase(View):
  
  fps = 60
  default_update_interval = 1/fps
  default_duration = 0.5
  
  current_gen = 'root'
  parent_gens = {}
  active_gens = set()
  standby_gens = {}
  activate = set()
  deactivate = set()
  
  def update(self):
    ''' Run active steppers, remove finished ones,
    activate next steppers. '''
    for gen in self.activate:
      self.active_gens.add(gen)
    for gen in self.deactivate:
      self.active_gens.remove(gen)
    self.activate = set()
    self.deactivate = set()
    gen_to_end = []
    for gen in self.active_gens:
      wait_time = None
      try:
        self.current_gen = gen
        wait_time = next(gen)
      except StopIteration:
        if gen not in self.deactivate:
          gen_to_end.append(gen)
      if wait_time is not None:
        if wait_time == 'wait':
          wait_time = self.default_duration
        if isinstance(wait_time, Number):
          self.timer(wait_time)
    self.current_gen = 'root'
    for gen in gen_to_end:
      self.active_gens.remove(gen)
      parent_gen = self.parent_gens[gen]
      del self.parent_gens[gen]
      if parent_gen != 'root':
        self.standby_gens[parent_gen].remove(gen)
        if len(self.standby_gens[parent_gen]) == 0:
          self.active_gens.add(parent_gen)
          del self.standby_gens[parent_gen]
    if len(self.active_gens) == 0:
      self.update_interval = 0.0

  def cancel(self, script):
    ''' Cancels any ongoing animations and
    sub-scrips for the given script. '''
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
      
    print(to_cancel)
    for gen in to_cancel:
      if gen == self.current_gen:
        self.currrent_gen = parent_gen
      del self.parent_gens[gen]
      self.activate.discard(gen)
      self.deactivate.discard(gen)
      self.active_gens.discard(gen)
      if gen in self.standby_gens:
        del self.standby_gens[gen]

  @script
  def timer(self, duration, action=None):
    ''' Acts as a wait timer. Optional action is
    called every cycle. '''
    start_time = time.time()
    dt = 0
    while dt < duration:
      if action: action(dt)
      yield
      dt = time.time() - start_time
      

class ScriptedPrimitives(ScriptedBase):
  
  ease_func_params = {
    'easeIn': (0, 0.05, 0.25, 1),
    'easeOut': (0, 0.75, 0.95, 1),
    'easeInOut': (0, 0.05, 0.95, 1),
    'easeOutIn': (0, 0.75, 0.25, 1),
    'easeInBounce': (0, -0.5, 0.25, 1),
    'easeOutBounce': (0, 0.75, 1.5, 1),
    'easeInOutBounce': (0, -0.5, 1.5, 1)
  }
  
  def cubic(self, params, t):
    u = params
    return u[0]*(1-t)**3 + 3*u[1]*(1-t)**2*t + 3*u[2]*(1-t)*t**2 + u[3]*t**3
  
  @script  
  def set_value(self, attribute, value, func=None, target=None):
    ''' Generator that sets the attribute to a value
    once, or several times if the value itself is
    a generator. '''
    target = target or self
    func = func if callable(func) else lambda val: val
    if isinstance(value, GeneratorType):
      while True:
        setattr(target, attribute, func(next(value)))
        yield
    elif hasattr(value, '__iter__') and not isinstance(value, str):
      iterator = iter(value)
      for value in iterator:
        setattr(target, attribute, func(value))
        yield
    else:
      setattr(target, attribute, func(value))
  
  @script  
  def slide_value(self, attribute, end_value, target=None, start_value=None, duration=ScriptedBase.default_duration, delta_func=None, ease_func=None, current_func=None, map_func=None):
    ''' Generator that "slides" the value of an
    attribute to an end value in a given duration.
    '''
    target = target or self
    start_value = start_value if start_value is not None else getattr(target, attribute)
    
    delta_func = delta_func if callable(delta_func) else lambda start_value, end_value: end_value - start_value
    map_func = map_func if callable(map_func) else lambda val: val
    if ease_func in self.ease_func_params:
      ease_func = partial(self.cubic, self.ease_func_params[ease_func])
    else:
      ease_func = ease_func if callable(ease_func) else lambda val: val
    current_func = current_func if callable(current_func) else lambda start_value, t_fraction, delta_value: start_value + t_fraction * delta_value
    
    delta_value = delta_func(start_value, end_value)
    start_time = time.time()
    dt = 0
    while dt < duration:
      t_fraction = ease_func(dt/duration)
      current_value = current_func(start_value, t_fraction, delta_value)
      setattr(target, attribute, map_func(current_value))
      yield
      dt = time.time() - start_time
    setattr(target, attribute, map_func(end_value))
  
  def slide_color(self, *args, **kwargs):

    def delta_func_for_color(start_value, end_value):
      start_color = parse_color(start_value)
      end_color = parse_color(end_value)
      return tuple((end_color[i] - start_color[i] for i in range(4)))
    def current_func_for_color(start_value, t_fraction, delta_color):
      start_color = parse_color(start_value)
      return tuple((start_color[i] + t_fraction * delta_color[i] for i in range(4)))
      
    delta_func = delta_func_for_color if 'delta_func' not in kwargs else kwargs['delta_func']
    current_func = current_func_for_color if 'current_func' not in kwargs else kwargs['current_func']
    
    return self.slide_value(*args, **kwargs, delta_func=delta_func, current_func=current_func)


class Scripted(ScriptedPrimitives):
  ''' Convenience functions for "pre-packaged"
  animation effects. '''

  @script
  def hide(self, view=None, **kwargs):
    ''' Fade the view away, then set as hidden '''  
    view = view or self 
    self.slide_value('alpha', 0.0, target=view, **kwargs)
    yield
    view.hidden = True

  @script 
  def show(self, view=None, **kwargs):
    ''' Unhide view, then fade in '''
    view = view or self
    view.hidden = False
    self.slide_value('alpha', 1.0, target=view, **kwargs)

  @script    
  def pause(self, duration=ScriptedBase.default_duration):
    ''' Wait a given amount of seconds. '''
    self.timer(duration)

  @script
  def pulse(self, color='#67cf70', view=None):
    view = view or self
    orig_color = view.background_color
    self.slide_color('background_color', color, ease_func='easeOut', target=view)
    yield
    self.slide_color('background_color', orig_color, ease_func='easeIn', target=view)

  @script    
  def move_to(self, x, y, view=None, **kwargs):
    ''' Move to x, y '''
    view = view or self
    self.slide_value('x', x, target=view, **kwargs)
    self.slide_value('y', y, target=view, **kwargs)

  @script    
  def rotate(self, degrees, view=None, rps=1, start_value=0, **kwargs):
    ''' Rotate view given degrees at given rps - rounds per second. Set start_value if not
    starting from 0. '''
    view = view or self
    duration = degrees / (rps * 360)
    radians = degrees/360*2*math.pi
    self.slide_value('transform', radians, start_value=start_value, map_func=lambda r: Transform.rotation(r), target=view, duration=duration, **kwargs)
    

if __name__ == '__main__':
  
  class DemoBackground(View):
    
    def __init__(self):
      self.start_point = (0,0)
      self.axes_counter = 0
      self.curve_point_x = None
      self.curve_point_y = None
      self.curve = []
    
    def draw(self):
      if self.axes_counter > 0:
        spx = self.start_point.x
        spy = self.start_point.y
        set_color('black')
        path = Path()
        path.move_to(spx, spy)
        path.line_to(spx+self.axes_counter, spy)          
        path.move_to(spx, spy)
        path.line_to(spx, spy-self.axes_counter)
        
        end_size = 10
        path.move_to(spx+self.axes_counter, spy)
        path.line_to(spx+self.axes_counter-end_size, spy-end_size)
        path.move_to(spx+self.axes_counter, spy)
        path.line_to(spx+self.axes_counter-end_size, spy+end_size)
        path.move_to(spx, spy-self.axes_counter)
        path.line_to(spx-end_size, spy-self.axes_counter+end_size)
        path.move_to(spx, spy-self.axes_counter)
        path.line_to(spx+end_size, spy-self.axes_counter+end_size)
        
        path.stroke()
        
        path = Path()
        set_color('#91cf96')
        path.move_to(spx, spy)
        
        if self.curve_point_x is not None:
          self.curve.append((spx+self.curve_point_x, spy-self.curve_point_y))
          
        for px, py in self.curve:
          path.line_to(px, py)

        path.stroke()
        
    def trigger_refresh(self, value):
      self.set_needs_display()
      return value
  
  v = DemoBackground()
  v.background_color = 'white'
  v.present('sheet')
  
  class Demo(Scripted):
    
    def __init__(self):
      self.frame = (100, 100, 150, 40)
      self.background_color = 'white'
      self.l = l = Label(text='Scripter Demo')
      l.flex = 'WH'
      l.text_color = 'black'
      l.alignment = ALIGN_CENTER
      self.add_subview(l)
      l.frame = self.bounds
      
      self.hidden = True
      
    @script
    def demo_script(self):
      # Convenience function to hide the view
      self.show()
      self.pulse()
      yield
      yield 'wait'
      self.move_to(200, 200)
      yield
      # Combine a primitive with a lambda and
      # target the contained Label instead of self
      self.set_value('text', range(1, 101), lambda count: f'Count: {count}', target=self.l)
      yield
      yield 'wait'
      # Transformations
      self.l.text = 'Rotating'
      self.rotate(720, ease_func='easeInOutBounce')
      self.slide_color('background_color', 'green', duration=2.0)
      self.slide_color('text_color', 'white', duration=2.0, target=self.l)
      yield
      yield 'wait'
      self.l.text = 'Move two'
      # Create another view and control it as well
      # Use another function to control animation
      # "tracks"
      self.other = View(background_color='red', frame=(10, 200, 150, 40))
      v.add_subview(self.other)
      self.sub_script()
      self.move_to(200, 300, view=self.other)
      yield
      self.l.text = 'Custom'
      yield 'wait'
      # Driving custom View.draw animation
      v.start_point = self.center
      self.set_value('axes_counter', range(1, 210, 3), target=v, func=v.trigger_refresh)
      yield
      yield 'wait'
      self.slide_value('curve_point_x', 200, start_value=1, target=v, duration=2.0)
      self.slide_value('curve_point_y', 200, start_value=1, target=v, ease_func='easeInOutBounce', map_func=v.trigger_refresh, duration=2.0)
      yield
      yield 'wait'
      self.slide_value('x', self.x+200, duration=2.0)
      self.slide_value('y', self.y-200, ease_func='easeInOutBounce', duration=2.0)
      yield
      self.l.text = 'Complete'
      self.pause(2.0)
      yield
      self.hide(view=v)
  
    @script
    def sub_script(self):
      self.move_to(50, 200)
      yield
      self.move_to(50, 300)        
      yield
      self.hide(view=self.other)
      yield
      v.remove_subview(self.other)
  
  s = Demo()
  v.add_subview(s)
  
  now_running = s.demo_script()
  
  def cancel_demo(sender):
    s.cancel(now_running)
  
  b = Button(title='Cancel')
  b.frame = (v.width-85, 10, 75, 40)
  b.background_color = 'black'
  b.tint_color = 'white'
  b.action = cancel_demo
  v.add_subview(b)
  
  
  #animations.hide_or_reveal_view(c)
