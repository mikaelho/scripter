#coding: utf-8

'''
# _SCRIPTER_ - Pythonista UI and Scene animations

![Logo](https://raw.githubusercontent.com/mikaelho/scripter/master/logo.jpg)

# Quick start

In order to start using the animation effects, just import scripter and call
the effects as functions:

    from scripter import *
    
    hide(my_button)
    
Effects expect an active UI view as the first argument. Effects run for a
default duration of 0.5 seconds, unless otherwise specified with a `duration` 
argument.

If you want to create a more complex animation from the effects provided,
combine them in a script:
  
    @script
    def my_effect(view):
      move(view, 50, 200)
      pulse(view, 'red')
      yield
      hide(view, duration=2.0)
      
Scripts control the order of execution with `yield` statements. Here movement
and a red pulsing highlight happen at the same time. After both actions are
completed, view fades away slowly, in 2 seconds.

As the view provided as the first argument can of course be `self` or `sender`,
scripts fit naturally as custom `ui.View` methods or `action` functions. 

As small delays are often needed for natural-feeling animations, you can append
a number after a `yield` statement, to suspend the execution of the script for
that duration, or `yield 'wait'` for the default duration.

Another key for good animations is the use of easing functions that modify how
the value progresses from starting value to the target value. Easing functions
support creating different kinds of accelerating, bouncing and springy effects.
Easing functions can be added as an argument to scripts:
  
    slide_value(view, 'x', 200, ease_func=bounce_out)
    
See this
[reference](https://raw.githubusercontent.com/mikaelho/scripter/master/ease-funcs.jpg)
to pick the right function, or run `scripter-demo.py` to try out the available
effects and to find the optimal duration and easing function combo for your purposes.

You can change the default speed of all animations by setting 
`Scripter.default_duration`.

Scripter can also be used to animate different kinds of Pythonista `scene`
module Nodes, including the Scene itself. Scripter provides roughly the same 
functionality as `scene.Action`, but is maybe a bit more concise, and is
available as an option if you want to use same syntax in both UI and Scene
projects.
        
See the API documentation for individual effects and how to roll your own with 
`set_value`, `slide_value` and `timer`.

There are also convenience functions, not separately documented, corresponding
to all animatable attributes of ui views. For example, you can animate the 
`ui.View.background_color` attribute with:
    
    background_color(view, 'black')
'''

from ui import *
from scene import Node, Scene
import scene_drawing
import objc_util, ctypes

from types import GeneratorType, SimpleNamespace
from numbers import Number
from functools import partial, wraps
from contextlib import contextmanager
import time, math

#docgen: Script management

def script(func):
  '''
  _Can be used with Scene Nodes._
  
  Decorator for the animation scripts. Scripts can be functions, methods or generators.
  
  First argument of decorated functions must always be the view to be animated.
  
  Calling a script starts the Scripter `update` loop, if not already running.
  
  New scripts suspend the execution of the parent script until all the parallel
  scripts have completed, after which the `update` method will resume the
  execution of the parent script.
  '''
  @wraps(func)
  def wrapper(view, *args, **kwargs):
    gen = func(view, *args, **kwargs)
    if not isinstance(gen, GeneratorType):
      return gen
    scr = find_scripter_instance(view)
    scr.view_for_gen[gen] = view
    scr.parent_gens[gen] = scr.current_gen
    if scr.current_gen != 'root':
      scr.standby_gens.setdefault(scr.current_gen, set())
      scr.standby_gens[scr.current_gen].add(gen)
      scr.deactivate.add(scr.current_gen)
    scr.activate.add(gen)
    scr.update_interval = scr.default_update_interval
    scr.running = True

    return gen
    
  return wrapper

def isfinished(gen):
  ''' Returns True if the generator argument has been exhausted, i.e.
  script has run to the end. '''
  return gen.gi_frame is None

def isnode(view):
  ''' Returns True if argument is an instance of a subclass of scene.Node. '''
  return issubclass(type(view), Node)
 
def find_scripter_instance(view):
  '''
  _Can be used with Scene Nodes._
  
  Scripts need a "controller" ui.View that runs the update method for them. This 
  function finds or creates the controller for a view as follows:
    
  1. Check if the view itself is a Scripter
  2. Check if any of the subviews is a Scripter
  3. Repeat 1 and 2 up the view hierarchy of superviews
  4. If not found, create an instance of Scripter as a hidden subview of the root view
  
  In case of scene Nodes, search starts from `node.scene.view`.
  
  If you want cancel or pause scripts, and have not explicitly created a
  Scripter instance to run them, you need to use this method first to find the
  right one.
  '''
  
  if isnode(view):
    if hasattr(view, 'view'):
      view = view.view # Scene root node
    else:
      if view.scene is None:
        raise ValueError('Node must be added to a Scene before animations')
      view = view.scene.view
      
  while view:
    if isinstance(view, Scripter):
      return view
    for subview in view.subviews:
      if isinstance(subview, Scripter):
        return subview
    parent = view.superview
    if parent:
      view = parent
    else:
      break
  # If not found, create a new one as a hidden
  # subview of the root view
  scr = Scripter(hidden=True)
  view.add_subview(scr)
  return scr

def find_root_view():
  ''' Locates the first `present`ed view. '''
  root_objc_view = objc_util.UIApplication.sharedApplication().windows()[0]
  for _ in range(5):
    root_objc_view = root_objc_view.subviews()[0]
  view = root_objc_view.pyObject(argtypes=[], restype=ctypes.py_object)
  return view

class Scripter(View):
  
  '''
  Class that contains the `update` method used to run the scripts and to control their execution.
  
  Runs at default 60 fps, or not at all when there are no scripts to run.
  
  Inherits from ui.View; constructor takes all the same arguments as ui.View.
  '''

  global_default_update_interval = 1/60
  default_duration = 0.5
      
  def __init__(self, *args, **kwargs):
    super().__init__(self, *args, **kwargs)
    self.default_update_interval = Scripter.global_default_update_interval
    self.cancel_all()
    self.running = False
    self.time_paused = 0
  
  @property
  def default_update_interval(self):
    '''
    The running rate for the update method. Frames per second is here considered to be just an
    alternative way of setting the update interval, and this property is linked to
    `default_fps` - change one and the other will change as well.
    '''
    return self._default_update_interval
    
  @default_update_interval.setter
  def default_update_interval(self, value):
    self._default_update_interval = value
    self._default_fps = 1/value
  
  @property
  def default_fps(self):
    '''
    The running rate for the update method. Frames per second is here considered to be just an
    alternative way of setting the update interval, and this property is linked to
    `default_update_interval` - change one and the other will change as well.
    '''
    return self._default_fps
    
  @default_fps.setter
  def default_fps(self, value):
    self._default_fps = value
    self._default_update_interval = 1/value
  
  def update(self):
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
      for script in self.cancel_queue:
        self._process_cancel(script)
      self.cancel_queue = set()
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
          timer(self.view_for_gen[gen], wait_time)
        else:
          wait_time = None
          try:
            wait_time = next(gen)
          except StopIteration:
            if gen not in self.deactivate:
              gen_to_end.append(gen)
          if wait_time is not None:
            if wait_time == 'wait':
              wait_time = self.default_duration
            if isinstance(wait_time, Number):
              self.should_wait[gen] = wait_time
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
    if len(self.active_gens) == 0:
      self.update_interval = 0.0
      self.running = False

  def pause_play_all(self):
    ''' Pause or play all animations. '''
    self.update_interval = 0 if self.update_interval > 0 else self.default_update_interval
    self.running = self.update_interval > 0
    if not self.running:
      self.pause_start_time = time.time()
    else:
      self.time_paused = time.time() - self.pause_start_time

  def cancel(self, script):
    ''' Cancels any ongoing animations and
    sub-scripts for the given script. '''
    self.cancel_queue.add(script)
    
  def _process_cancel(self, script):
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
        self.currrent_gen = parent_gen
      del self.view_for_gen[gen]
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
    self.view_for_gen = {}
    self.should_wait = {}
    self.parent_gens = {}
    self.active_gens = set()
    self.standby_gens = {}
    self.activate = set()
    self.deactivate = set()
    self.running = False
    self.cancel_queue = set()
  
  @staticmethod
  def _cubic(params, t):
    '''
    Cubic function for easing animations.
    
    Arguments:
      
    * params - either a 4-tuple of cubic parameters, one of the parameter names below (like ’easeIn') or 'linear' for a straight line
    * t - time running from 0 to 1
    '''
    ease_func_params = {
      'easeIn': (0, 0.05, 0.25, 1),
      'easeOut': (0, 0.75, 0.95, 1),
      'easeInOut': (0, 0.05, 0.95, 1),
      'easeOutIn': (0, 0.75, 0.25, 1),
      'easeInBounce': (0, -0.5, 0.25, 1),
      'easeOutBounce': (0, 0.75, 1.5, 1),
      'easeInOutBounce': (0, -0.5, 1.5, 1)
    }
    
    if isinstance(params, str):
      if params == 'linear':
        return t
      try:
        u = ease_func_params[params]
      except KeyError:
        raise ValueError('Easing function name must be one of the following: ' + ', '.join(list(ease_func_params)))
    else:
      u = params
    return u[0]*(1-t)**3 + 3*u[1]*(1-t)**2*t + 3*u[2]*(1-t)*t**2 + u[3]*t**3

def cancel(view, handle):
    scr = find_scripter_instance(view)
    scr.cancel(handle)
  
#docgen: Animation primitives
  
@script  
def set_value(view, attribute, value, func=None):
  '''
  Generator that sets the `attribute` to a `value` once, or several times if the value itself is a 
  generator or an iterator.
  
  Optional keyword parameters:
  
  * `func` - called with the value, returns the actual value to be set
  '''
    
  func = func if callable(func) else lambda val: val
  if isinstance(value, GeneratorType):
    while True:
      setattr(view, attribute, func(next(value)))
      yield
  elif hasattr(value, '__iter__') and not isinstance(value, str):
    iterator = iter(value)
    for value in iterator:
      setattr(view, attribute, func(value))
      yield
  else:
    setattr(view, attribute, func(value))

@script  
def slide_value(view, attribute, end_value, target=None, start_value=None, duration=None, delta_func=None, ease_func=None, current_func=None, map_func=None, side_func=None):
  '''
  Generator that "slides" the `value` of an
  `attribute` to an `end_value` in a given duration.
  
  Optional keyword parameters:
  
  * `start_value` - set if you want some other value than the current value of the attribute as the animation start value.
  * `duration` - time it takes to change to the target value. Default is 0.5 seconds.
  * `delta_func` - use to transform the range from start_value to end_value to something else.
  * `ease_func` - provide to change delta-t value to something else. Mostly used for easing; you can provide an easing function name as a string instead of an actual function. See supported easing functions [here](https://raw.githubusercontent.com/mikaelho/scripter/master/ease-functions.png).
  * `current_func` - Given the start value, delta value and progress fraction (from 0 to 1), returns the current value. Intended to be used to manage more exotic values like colors.
  * `map_func` - Used to translate the current value to something else, e.g. an angle to a Transform.rotation.
  * `side_func` - Called without arguments each time after the main value has been set. Useful for side effects.
  '''
  scr = find_scripter_instance(view)
  duration = duration or scr.default_duration
  start_value = start_value if start_value is not None else getattr(view, attribute)
  
  delta_func = delta_func if callable(delta_func) else lambda start_value, end_value: end_value - start_value
  map_func = map_func if callable(map_func) else lambda val: val
  if isinstance(ease_func, str) or isinstance(ease_func, tuple):
    ease_func = partial(Scripter._cubic, ease_func)
  else:
    ease_func = ease_func if callable(ease_func) else lambda val: val
  current_func = current_func if callable(current_func) else lambda start_value, t_fraction, delta_value: start_value + t_fraction * delta_value
  
  delta_value = delta_func(start_value, end_value)
  start_time = time.time()
  dt = 0
  scaling = True
  while scaling:
    if dt < duration:
      t_fraction = ease_func(dt/duration)
      #print(ease_func.__name__, t_fraction)
    else:
      t_fraction = ease_func(1)
      scaling = False
    current_value = current_func(start_value, t_fraction, delta_value)
    setattr(view, attribute, map_func(current_value))
    if side_func: side_func()
    yield
    if scr.time_paused > 0:
      start_time += scr.time_paused
    dt = time.time() - start_time

@script
def slide_tuple(view, *args, **kwargs):
  '''
  Slide a tuple value of arbitrary length. Supports same arguments as `slide_value`. '''
  def delta_func_for_tuple(start_value, end_value):
    return tuple((end_value[i] - start_value[i] for i in range(len(start_value))))
  def current_func_for_tuple(start_value, t_fraction, delta_value):
    return tuple((start_value[i] + t_fraction * delta_value[i] for i in range(len(start_value))))
    
  delta_func = delta_func_for_tuple if 'delta_func' not in kwargs else kwargs['delta_func']
  current_func = current_func_for_tuple if 'current_func' not in kwargs else kwargs['current_func']
  
  return slide_value(view, *args, **kwargs, delta_func=delta_func, current_func=current_func)
  
@script
def slide_color(view, attribute, end_value, **kwargs):
  ''' Slide a color value. Supports the same
  arguments as `slide_value`. '''
  start_value = kwargs.pop('start_value', None)
  if start_value:
    start_value = parse_color(start_value)
  end_value = parse_color(end_value)
  
  return slide_tuple(view, attribute, end_value, start_value=start_value, **kwargs)

@script
def timer(view, duration=None, action=None):
  ''' Acts as a wait timer for the given duration in seconds. `view` is only used to find the 
  controlling Scripter instance. Optional action function is called every cycle. '''
  
  scr = find_scripter_instance(view)
  duration = duration or scr.default_duration
  start_time = time.time()
  dt = 0
  while dt < duration:
    if action: action()
    yield
    if scr.time_paused > 0:
      start_time += scr.time_paused
    dt = time.time() - start_time


#docgen: Animation effects

@script    
def center(view, move_center_to, **kwargs):
  ''' Move view center (anchor for Scene Nodes). '''
  attr = 'position' if isnode(view) else 'center'
  return slide_tuple(view, attr, move_center_to, **kwargs)
  
@script
def center_to(view, move_center_to, **kwargs):
  ''' Alias for `center`. '''
  return center(view, move_center_to, **kwargs)
  
@script    
def center_by(view, dx, dy, **kwargs): 
  ''' Adjust view center/anchor position by dx, dy. '''
  cx, cy = view.position if isnode(view) else view.center
  return center(view, (cx + dx, cy + dy), **kwargs)

@script
def expand(view, **kwargs):
  '''  _Not applicable for Scene Nodes._
  
  Expands the view to fill all of its superview. '''
  move(view, 0, 0, **kwargs)
  slide_value(view, 'width', view.superview.width, **kwargs)
  slide_value(view, 'height', view.superview.height, **kwargs)
  yield 

@script
def fly_out(view, direction, **kwargs):
  ''' Moves the view out of the screen in the given direction. Direction is one of the
  following strings: 'up', 'down', 'left', 'right'. '''
  
  (sw,sh) = get_screen_size()
  if isnode(view):
    (lx, ly, lw, lh) = view.scene.bounds
    attr = 'position'
    if direction == 'up':
      direction = 'down'
    elif direction == 'down':
      direction = 'up'
  else:
    (lx, ly, lw, lh) = convert_rect(rect=(0,0,sw,sh), to_view=view)
    attr = 'center'
  (x,y,w,h) = view.frame
  (cx, cy) = getattr(view, attr)
  targets = { 'up': (cx,ly-h), 'down': (cx,lh+h), 'left': (lx-w,cy), 'right': (lw+w,cy) }
  try:
    target_coord = targets[direction]
  except KeyError:
    raise ValueError('Direction must be one of ' + str(list(targets.keys())))
  return slide_tuple(view, attr, target_coord, **kwargs)

def future(future):
  ''' yields until the given future is completed. '''
  @script
  def wait_for_done(view, future):
    while not future.done():
      yield
    if future.exception() is not None:
      raise future.exception()
  return wait_for_done(find_root_view(), future)

@script
def hide(view, **kwargs):
  ''' Fade the view away. '''  
  return slide_value(view, 'alpha', 0.0, **kwargs)

@script    
def move(view, x, y, **kwargs):
  ''' Move to x, y.
  For UI views, this positions the top-left corner.
  For Scene Nodes, this moves the Node `position`. '''
  if isnode(view):
    slide_tuple(view, 'position', (x,y), **kwargs)
  else:
    slide_value(view, 'x', x, **kwargs)
    slide_value(view, 'y', y, **kwargs)
  yield 
  
@script 
def move_to(view, x, y, **kwargs):
  ''' Alias for `move`. '''
  return move(view, x, y, **kwargs)
  
@script    
def move_by(view, dx, dy, **kwargs):
  ''' Adjust position by dx, dy. '''
  if isnode(view):
    slide_tuple(view, 'position', (view.position.x+dx, view.position.y+dy), **kwargs)
  else:
    slide_value(view, 'x', view.x + dx, **kwargs)
    slide_value(view, 'y', view.y + dy, **kwargs)
  yield

@script
def pulse(view, color='#67cf70', **kwargs):
  '''  Pulses the background of the view to the given color and back to the original color.
  Default color is a shade of green. '''
  root_func = kwargs.pop('ease_func', ease_in)
  ease_func = partial(mirror, root_func)
  return slide_color(view, 'background_color', color, ease_func=ease_func, **kwargs)

@script
def reveal_text(view, **kwargs):
  ''' Reveals text one letter at a time in the given duration. View must have a `text` attribute. '''
  full_text = view.text
    
  return slide_value(view, 'text', len(full_text), start_value=0, map_func=lambda value: full_text[:max(0, min(len(full_text), round(value)))], **kwargs)

@script
def roll_to(view, to_center, end_right_side_up=True, **kwargs):
  ''' Roll the view to a target position given by the `to_center` tuple. If `end_right_side_up` is true, view starting angle is adjusted so that the view will end up with 0 rotation at the end, otherwise the view will start as-is, and end in an angle determined by the roll.
  View should be round for the rolling effect to make sense. Imaginary rolling surface is below the view - or to the left if rolling directly downwards. '''
  from_center = view.position if isnode(view) else view.center
  roll_vector = Vector(to_center)-Vector(from_center)
  roll_direction = 1 if roll_vector.x >= 0 else -1
  roll_distance = roll_vector.magnitude
  view_r = view.frame[0]/2
  roll_degrees = roll_direction * 360 * roll_distance/(2*math.pi*view_r)
  if end_right_side_up:
    start_degrees = roll_direction * (360 - abs(roll_degrees) % 360)
    start_radians = math.radians(start_degrees)
    if isnode(view):
      view.rotation = start_radians
    else:
      view.transform = Transform.rotation(start_radians)
  rotate_by(view, roll_degrees, **kwargs)
  center(view, to_center, **kwargs)
  yield

@script    
def rotate(view, degrees, shortest=False, **kwargs):
  ''' Rotate view to an absolute angle. Set start_value if not starting from 0. Positive number rotates clockwise. For UI views, does not mix with other transformations.
  
  Optional arguments:
    
  * `shortest` - If set to True (default), will turn in the "right" direction. For UI views, start_value must be set to a sensible value for this to work.
  '''
  start_value = kwargs.pop('start_value', math.degrees(view.rotation) if isnode(view) else 0)
  radians = math.radians(degrees)
  start_radians = math.radians(start_value)
  if shortest:
    degrees = math.degrees(math.atan2(math.sin(radians-start_radians), math.cos(radians-start_radians)))
    rotate_by(view, degrees)
  else:
    if isnode(view):
      return slide_value(view, 'rotation', radians, start_value=start_radians, **kwargs)
    else:
      return slide_value(view, 'transform', radians, start_value=start_radians, map_func=lambda r: Transform.rotation(r), **kwargs)
  
def rotate_to(view, degrees, **kwargs):
  ''' Alias for `rotate`. '''
  return rotate(view, degrees, **kwargs)
  
@script    
def rotate_by(view, degrees, **kwargs):
  ''' Rotate view by given degrees. '''
  radians = math.radians(degrees)
  if isnode(view):
    return slide_value(view, 'rotation', view.rotation+radians, start_value=view.rotation, **kwargs)
  else:
    starting_transform = view.transform
    return slide_value(view, 'transform', radians, start_value=0, map_func=lambda r: Transform.rotation(r) if not starting_transform else starting_transform.concat(Transform.rotation(r)), **kwargs)
  
@script    
def scale(view, factor, **kwargs):
  ''' Scale view to a given factor in both x and y dimensions. For UI views, you need to explicitly set `start_value` if not starting from 1. '''
  if isnode(view):
    start_value = kwargs.pop('start_value', view.x_scale)
    slide_value(view, 'x_scale', factor, start_value=start_value, **kwargs)
    slide_value(view, 'y_scale', factor, start_value=start_value, **kwargs)
  else:
    start_value = kwargs.pop('start_value', 1)
    slide_value(view, 'transform', factor, start_value=start_value, map_func=lambda r: Transform.scale(r, r), **kwargs)
  yield

def scale_to(view, factor, **kwargs):
  ''' Alias for `scale`. '''
  return scale(view, factor, **kwargs)

@script    
def scale_by(view, factor, **kwargs):
  ''' Scale view relative to current scale factor. '''
  if isnode(view):
    start_value = kwargs.pop('start_value', view.x_scale)
    end_value = start_value * factor
    slide_value(view, 'x_scale', end_value, start_value=start_value, **kwargs)
    slide_value(view, 'y_scale', end_value, start_value=start_value, **kwargs)
  else:
    start_value = kwargs.pop('start_value', 1)
    starting_transform = view.transform
    slide_value(view, 'transform', factor, start_value=start_value, map_func=lambda r: Transform.scale(r, r) if not starting_transform else starting_transform.concat(Transform.scale(r, r)), **kwargs)
  yield

@script 
def show(view, **kwargs):
  ''' Slide alpha from 0 to 1. '''
  view.alpha = 0.0
  return slide_value(view, 'alpha', 1.0, **kwargs)

@script
def wobble(view):
  ''' Little wobble of a view, intended to attract attention. '''
  return rotate(view, 10, shortest=False, duration=0.3, ease_func=oscillate)

@script
def wait_for_tap(view):
    ''' Overlays the given view with a temporary transparent view, and
    yields until the view is tapped. '''
    
    class WaitForTap(View):
    
        def __init__(self, target, **kwargs):
            super().__init__(**kwargs)
            self.tapped = False
            self.background_color = (0,0,0,0.0001)
            self.frame=target.bounds
            target.add_subview(self)
                
        def touch_ended(self, touch):
            self.tapped = True
    
    t = WaitForTap(view)
    while not t.tapped:
        yield
        
# Generate convenience functions

animation_attributes = (
    (slide_value, (
        'alpha',
        'corner_radius',
        'height',
        'row_height',
        'value',
        'width',
        'x',
        'y',
    )),
    (slide_color, (
        'background_color',
        'bar_tint_color',
        'border_color',
        'text_color',
        'tint_color',
        'title_color',
    )),
    (slide_tuple, (
        'bounds',
        'content_inset',
        'content_offset',
        'content_size',
        'frame',
        'scroll_indicator_insets',
        'selected_range',
    ))
)

for animation_function, keys in animation_attributes:
    for key in keys:
        def f(func, attr, view, value, **kwargs):
            func(view, attr, value, **kwargs)
        globals()[key] = partial(f, animation_function, key)

def while_not_finished(gen, scr, view, *args, **kwargs):
  ''' While `gen` is not finished, calls `scr` repeatedly with `view` and other
  arguments. '''
  @script
  def waiting(view, gen, scr, *args, **kwargs):
    while not isfinished(gen):
      scr(view, *args, **kwargs)
      yield
  waiting(view, gen, scr, *args, **kwargs)


class ScrollingBannerLabel(View):
  ''' UI component that scrolls the given text indefinitely, in either direction. Will only scroll if the text is too long to fit into this component.
  '''
  
  def __init__(self, **kwargs):
    ''' In addition to normal `ui.View` arguments, you can include:
      
    * `text` - To be scrolled as a marquee.
    * Label formatting arguments `font` and `text_color`.
    * `initial_delay` - How long we wait before we start scrolling, to enable reading the beginning of the text. Default is 2 seconds.
    * `scrolling_speed` - How fast the text moves, in points per second. Default is 100 pts/s.
    * `to_right` - Set to True if you would like the text to scroll from the left. Default is False.
    '''
    
    self.kwargs = {}
    self.scrolling_speed = kwargs.pop('scrolling_speed', 100)
    self.initial_delay = kwargs.pop('initial_delay', 2.0)
    self._direction = -1 if kwargs.pop('to_right', False) else 1
    if 'font' in kwargs: self.kwargs['font'] = kwargs.pop('font')
    if 'text_color' in kwargs: self.kwargs['text_color'] = kwargs.pop('text_color')
    
    super().__init__(**kwargs)
    
    self.text = kwargs.pop('text', None)
    
  @property
  def text(self):
    ''' You can change the text displayed at
    any point after initialization by setting
    this property. '''
    return self._text
    
  @text.setter
  def text(self, value):
    if value is not None and len(value) > 0:
      value = value.strip() + ' '
    self._text = value
    self._create_labels()
    
  def stop(self):
    ''' Stops the scrolling and places the text at start. '''
    scr = find_scripter_instance(self)
    scr.cancel(self._scroller)
    self.bounds = (0, 0, self.width, self.height)
    
  def restart(self):
    ''' Restarts the scrolling, including the initial delay, if any. '''
    self.stop()
    self._create_labels()
    
  def _create_labels(self):
    for view in self.subviews:
      self.remove_subview(view)
    self._text_width = 0
    self._total_width = 0
    if self._text is None or len(self._text) == 0: return
    
    l = Label(text=self._text, **self.kwargs)
    l.size_to_fit()
    l.x, l.y = 0, 0
    self.add_subview(l)
    self._text_width = self._total_width = l.width
    if self._total_width < self.width:
      return
      
    l = Label(text=self._text, **self.kwargs)
    l.size_to_fit()
    l.x, l.y = self._direction * self._total_width, 0
    self._total_width += l.width
    self.add_subview(l)
    self._scroller = self._start_scrolling()
    
  @script
  def _start_scrolling(self):
    duration = self._text_width/self.scrolling_speed
    timer(self, self.initial_delay)
    yield
    while True:
      bounds(self, (self._direction * self._text_width, 0, self.width, self.height), duration=duration)
      yield
      self.bounds = (0, 0, self.width, self.height)
      

#docgen: Easing functions

def linear(t):
  return t 
def sinusoidal(t):
  return scene_drawing.curve_sinodial(t)
def ease_in(t):
  return scene_drawing.curve_ease_in(t)
def ease_out(t):
  return scene_drawing.curve_ease_out(t)
def ease_in_out(t):
  return scene_drawing.curve_ease_in_out(t)
def ease_out_in(t):
  return Scripter._cubic('easeOutIn', t)
def elastic_out(t):
  return scene_drawing.curve_elastic_out(t)
def elastic_in(t):
  return scene_drawing.curve_elastic_in(t)
def elastic_in_out(t):
  return scene_drawing.curve_elastic_in_out(t)
def bounce_out(t):
  return scene_drawing.curve_bounce_out(t)
def bounce_in(t):
  return scene_drawing.curve_bounce_in(t)
def bounce_in_out(t):
  return scene_drawing.curve_bounce_in_out(t)
def ease_back_in(t):
  return scene_drawing.curve_ease_back_in(t)
def ease_back_in_alt(t):
  return Scripter._cubic('easeInBounce', t)
def ease_back_out(t):
  return scene_drawing.curve_ease_back_out(t)
def ease_back_out_alt(t):
  return Scripter._cubic('easeOutBounce', t)
def ease_back_in_out(t):
  return scene_drawing.curve_ease_back_in_out(t)
def ease_back_in_out_alt(t):
  return Scripter._cubic('easeInOutBounce', t)

def mirror(ease_func, t):
  ''' Runs the given easing function to the end in half the duration, then
  backwards in the second half. For example, if the function provided is
  `linear`, this function creates a "triangle" from 0 to 1, then back to 0;
  if the function is `ease_in`, the result is more of a "spike".'''
  ease_func = ease_func if callable(ease_func) else partial(Scripter._cubic, ease_func)
  if t < 0.5:
    t /= 0.5
    return ease_func(t)
  else:
    t -= 0.5
    t /= 0.5
    return ease_func(1-t)

def mirror_ease_in(t):
  return mirror(ease_in, t)
  
def mirror_ease_in_out(t):
  return mirror(ease_in_out, t)

def oscillate(t):
  ''' Basic sine curve that runs from 0 through 1, 0 and -1, and back to 0. '''
  return math.sin(t*2*math.pi)
  

class Vector (list):
  ''' Simple 2D vector class to make vector operations more convenient. If 
  performance is a concern, you are probably better off looking at numpy.
  
  Supports the following operations:
    
  * Initialization from two arguments, two keyword  arguments (`x` and `y`),
  tuple, list, or another Vector.
  * Equality and unequality comparisons to other vectors. For floating point
  numbers, equality tolerance is 1e-10.
  * `abs`, `int` and `round`
  * Addition and in-place addition
  * Subtraction
  * Multiplication and division by a scalar
  * `len`, which is the same as `magnitude`, see below.
  
  Sample usage:
    
      v = Vector(x = 1, y = 2)
      v2 = Vector(3, 4)
      v += v2
      assert str(v) == '[4, 6]'
      assert v / 2.0 == Vector(2, 3)
      assert v * 0.1 == Vector(0.4, 0.6)
      assert v.distance_to(v2) == math.sqrt(1+4)
    
      v3 = Vector(Vector(1, 2) - Vector(2, 0)) # -1.0, 2.0
      v3.magnitude *= 2
      assert v3 == [-2, 4]
    
      v3.radians = math.pi # 180 degrees
      v3.magnitude = 2
      assert v3 == [-2, 0]
      v3.degrees = -90
      assert v3 == [0, -2]
  '''

  abs_tol = 1e-10

  def __init__(self, *args, **kwargs):
    x = kwargs.pop('x', None)
    y = kwargs.pop('y', None)

    if x and y:
      self.append(x)
      self.append(y)
    elif len(args) == 2:
      self.append(args[0])
      self.append(args[1])
    else:
      super().__init__(*args, **kwargs)

  @property
  def x(self):
    ''' x component of the vector. '''
    return self[0]

  @x.setter
  def x(self, value):
    self[0] = value

  @property
  def y(self):
    ''' y component of the vector. '''
    return self[1]

  @y.setter
  def y(self, value):
    self[1] = value

  def __eq__(self, other):
    return math.isclose(self[0], other[0], abs_tol=self.abs_tol) and math.isclose(self[1], other[1], abs_tol=self.abs_tol)
    
  def __ne__(self, other):
    return not self.__eq__(other)

  def __abs__(self):
    return type(self)(abs(self.x), abs(self.y))

  def __int__(self):
    return type(self)(int(self.x), int(self.y))

  def __add__(self, other):
    return type(self)(self.x + other.x, self.y + other.y)
    
  def __iadd__(self, other):
    self.x += other.x
    self.y += other.y
    return self

  def __sub__(self, other):
    return type(self)(self.x - other.x, self.y - other.y)

  def __mul__(self, other):
    return type(self)(self.x * other, self.y * other)

  def __truediv__(self, other):
    return type(self)(self.x / other, self.y / other)

  def __len__(self):
    return self.magnitude
    
  def __round__(self):
    return type(self)(round(self.x), round(self.y))

  def dot_product(self, other):
    ''' Sum of multiplying x and y components with the x and y components of another vector. '''
    return self.x * other.x + self.y * other.y

  def distance_to(self, other):
    ''' Linear distance between this vector and another. '''
    return (Vector(other) - self).magnitude

  @property
  def magnitude(self):
    ''' Length of the vector, or distance from (0,0) to (x,y). '''
    return math.hypot(self.x, self.y)

  @magnitude.setter
  def magnitude(self, m):
    r = self.radians
    self.polar(r, m)

  @property
  def radians(self):
    ''' Angle between the positive x axis and this vector, in radians. '''
    #return round(math.atan2(self.y, self.x), 10)
    return math.atan2(self.y, self.x)

  @radians.setter
  def radians(self, r):
    m = self.magnitude
    self.polar(r, m)

  def polar(self, r, m):
    ''' Set vector in polar coordinates. `r` is the angle in radians, `m` is vector magnitude or "length". '''
    self.y = math.sin(r) * m
    self.x = math.cos(r) * m
    
  @property
  def degrees(self):
    ''' Angle between the positive x axis and this vector, in degrees. '''
    return math.degrees(self.radians)

  @degrees.setter
  def degrees(self, d):
    self.radians = math.radians(d)
    
  def steps_to(self, other, step_magnitude=1.0):
    """ Generator that returns points on the line between this and the other point, with each step separated by `step_magnitude`. Does not include the starting point. """
    if self == other:
      yield other
    else:
      step_vector = other - self
      steps = math.floor(step_vector.magnitude/step_magnitude)
      step_vector.magnitude = step_magnitude
      current_position = Vector(self)
      for _ in range(steps):
        current_position += step_vector
        yield Vector(current_position)
      if current_position != other:
        yield other
        
  def rounded_steps_to(self, other, step_magnitude=1.0):
    ''' As `steps_to`, but returns points rounded to the nearest integer. '''
    for step in self.steps_to(other):
      yield round(step)
      

if __name__ == '__main__':
  
  import editor, scene_drawing
  
  class DemoBackground(View):
    
    def __init__(self):
      self.start_point = (0,0)
      self.axes_counter = 0
      self.curve_point_x = None
      self.curve_point_y = None
      self.curve = []
      self.hide_curve = False
    
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
          
        if not self.hide_curve:
          for px, py in self.curve:
            path.line_to(px, py)

        path.stroke()
        
    def trigger_refresh(self, value):
      self.set_needs_display()
      return value
  
  v = DemoBackground()
  v.background_color = 'white'
  v.present('full_screen')
  
  class Demo(View):
    
    def __init__(self, *args, **kwargs):
      super().__init__(self, *args, *kwargs)
      self.frame = (100, 100, 150, 40)
      self.background_color = 'white'
      self.c = c = View(frame=(0,0,10,10))
      c.corner_radius = 5
      c.center = (15, 20)
      c.hidden = True
      c.background_color = 'black'
      self.l = l = Label(text='Scripter Demo')
      l.flex = 'WH'
      l.text_color = 'black'
      l.alignment = ALIGN_CENTER
      self.add_subview(c)
      self.add_subview(l)
      l.frame = self.bounds
      self.tv = tv = TextView(background_color='white')
      tv.text = editor.get_text()
      tv.text_color = '#4a4a4a'
      tv.frame = (2, 2, 146, 36)
      tv.flex = 'WH'
      tv.alpha = 0
      self.add_subview(tv)
      #self.hidden = True
      
    @script
    def demo_script(self):
      show(self)
      pulse(self, duration=1.0)
      yield 'wait'
      move(self, 200, 200)
      yield
      # Combine a primitive with a lambda and
      # target the contained Label instead of self
      set_value(self.l, 'text', range(1, 101), lambda count: f'Count: {count}')
      yield 1
      # Transformations
      self.l.text = 'Rotating'
      rotate(self, -720, ease_func=ease_back_in_out, duration=1.5)
      #slide_color(self, 'background_color', 'green', duration=2.0)
      background_color(self, 'green', duration=2.0)
      slide_color(self.l, 'text_color', 'white', duration=2.0)
      yield 'wait'
      self.l.text = 'Move two'
      # Create another view and control it as well
      # Use another function to control animation
      # "tracks"
      self.other = View(background_color='red', frame=(10, 200, 150, 40))
      v.add_subview(self.other)
      self.sub_script()
      move(self.other, 200, 400)
      yield 'wait'
      
      self.l.text = 'Custom'
      # Driving custom View.draw animation
      self.c.hidden = False
      background_color(self, 'transparent')
      text_color(self.l, 'black')
      v.start_point = SimpleNamespace(x=self.x+15, y=self.y+20)
      set_value(v, 'axes_counter', range(1, 210, 3), func=v.trigger_refresh)
      yield 'wait'
      slide_value(v, 'curve_point_x', 200, start_value=1, duration=2.0)
      slide_value(v, 'curve_point_y', 200, start_value=1, ease_func=ease_back_in_out, map_func=v.trigger_refresh, duration=2.0)
      yield 'wait'
      
      x(self, self.x+200, duration=2.0)
      y(self, self.y-200, ease_func=ease_back_in_out, duration=2.0)
      yield 'wait'
      
      self.l.text = 'Bounce'
      self.c.hidden = True
      background_color(self, 'green')
      text_color(self.l, 'white')
      width(self, 76)      
      height(self, 76)
      corner_radius(self, 38)
      v.hide_curve = True
      v.set_needs_display()
      yield
      x(self, v.start_point.x, ease_func='easeOut', duration=2.0)
      y(self, v.start_point.y-self.height, ease_func=scene_drawing.curve_bounce_out, duration=2.0)
      yield 1.0
      
      self.l.text = 'Roll'
      yield 'wait'
      roll_to(self, (self.center[0]+170, self.center[1]), duration=2.0)
      yield 1.0
      roll_to(self, (self.center[0]-170, self.center[1]), duration=2.0)
      yield 1.0
      
      v.axes_counter = 0
      v.set_needs_display()
      self.c.hidden = True
      expand(self)
      corner_radius(self, 0)
      background_color(self, 'white')
      show(self.tv)
      content_offset(self.tv, (0,0))
      yield 1.0
      
      content_offset(self.tv, (0, self.tv.content_size[1]), duration=20)
      self.end_fade()
  
    @script
    def sub_script(self):
      move(self, 50, 200)
      yield
      move(self, 50, 400)        
      yield
      hide(self.other)
      fly_out(self.other, 'down')
      yield
      v.remove_subview(self.other)
      
    @script
    def end_fade(self):
      yield 7.0
      hide(v)
      
  
  s = Demo()
  v.add_subview(s)
  
  now_running = s.demo_script()
  scr = find_scripter_instance(s)
  
  def pause_action(sender):
    scr.pause_play_all()
    pause.title = 'Pause' if scr.running else 'Play'
  
  pause = Button(title='Pause')
  pause.frame = (v.width-85, 60, 75, 40)
  pause.background_color = 'black'
  pause.tint_color = 'white'
  pause.action = pause_action
  v.add_subview(pause)
  
  def cancel_demo(sender):
    scr.cancel(now_running)
    hide(pause)
    hide(sender)
    # or could just use
    # scr.cancel_all()
    # if clear that nothing else will be running
  
  b = Button(title='Cancel')
  b.frame = (v.width-85, 10, 75, 40)
  b.background_color = 'black'
  b.tint_color = 'white'
  b.action = cancel_demo
  v.add_subview(b)
  
  m = ScrollingBannerLabel(text='This is a scripter test, with an info text that is too long to fit on screen at once.', font=('Futura', 24), text_color='green', frame=(40, v.height-50, v.width-80, 40))
  v.add_subview(m)
