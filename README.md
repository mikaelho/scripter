# _SCRIPTER_ - Pythonista UI animations

![Logo](https://raw.githubusercontent.com/mikaelho/scripter/master/logo.jpg)

# Quick start

In order to start using the animation effects, just import scripter and call the effects as functions:

    from scripter import *
    
    hide(my_button)
    
Effects expect an active UI view as the first argument. This can well be `self` or `sender` 
where applicable.

If you want to create a more complex animation from the effects provided, combine them in a
script:
  
    @script
    def my_script():
      move_to(my_button, 50, 200)
      pulse(my_button, 'red')
      yield
      hide(my_button)
      
Scripts control the order of execution with `yield` statements. Here movement and a red 
pulsing highlight happen at the same time. After both actions are completed, `my_button` fades 
away.
        
Run scripter.py in Pythonista to see a demo of most of the available effects.
        
See the API documentation for individual effects and how to roll your own with `set_value`, 
`slide_value` and `timer`.

_Note_: As of Sep 15, 2017, ui.View.update is only available in Pythonista 3 beta.

# Classes

## Class: Scripter

Class that contains the update method used to run the scripts and to control their execution
order.

Runs at default 60 fps, or not at all when there are no scripts to run.

Inherits from ui.View; constructor takes all the same arguments as ui.View.

### Methods:


#### `@property default_update_interval(self)`


#### `@default_update_interval.setter default_update_interval(self, value)`


#### `@property default_fps(self)`


#### `@default_fps.setter default_fps(self, value)`


#### ` update(self)`

  Run active steppers, remove finished ones,
  activate next steppers. 

#### ` pause_play_all(self)`

  Pause or play all animations. 

#### ` cancel(self, script)`

  Cancels any ongoing animations and
  sub-scripts for the given script. 

#### ` cancel_all(self)`

  Initializes all internal structures.
  Used at start and to cancel all running scripts.
# Functions


#### SCRIPT MANAGEMENT
#### ` script(func)`

  Decorator for the animation scripts. Scripts can be functions, methods or generators.
  
  First argument of decorated functions must always be the view to be animated.

#### ` find_scripter_instance(view)`

  Scripts need a "controller" ui.View that runs the update method for them. This function finds 
  or creates the controller for a view as follows:
    
  1. Check if the view itself is a Scripter
  2. Check if any of the subviews is a Scripter
  3. Repeat 1 and 2 up the view hierarchy of superviews
  4. If not found, create an instance of Scripter as a hidden subview of the root view
  
  If you want cancel or pause scripts, and have not explicitly created a Scripter instance to 
  run them, you need to use this method first to find the right one.

#### PRIMITIVES
#### `@script timer(view, duration, action=None)`

  Acts as a wait timer for the given duration in seconds. `view` is only used to find the 
  controlling Scripter instance. Optional action function is called every cycle. 

#### `@script set_value(view, attribute, value, func=None)`

  Generator that sets the `attribute` to a `value` once, or several times if the value itself is a 
  generator or an iterator.
  
  Optional keyword parameters:
  
  * `func` - called with the value, returns the actual value to be set

#### `@script slide_value(view, attribute, end_value, target=None, start_value=None, duration=None, delta_func=None, ease_func=None, current_func=None, map_func=None)`

  Generator that "slides" the `value` of an
  `attribute` to an `end_value` in a given duration.
  
  Optional keyword parameters:
  
  * `start_value` - set if you want some other value than the current value of the attribute as the animation start value.
  * `duration` - time it takes to change to the target value. Default is 0.5 seconds.
  * `delta_func` - use to transform the range from start_value to end_value to something else.
  * `ease_func` - provide to change delta-t value to something else. Mostly used for easing; you can provide an easing function name as a string instead of an actual function. See supported easing functions [here](https://raw.githubusercontent.com/mikaelho/scripter/master/ease-functions.png).
  * `current_func` - Given the start value, delta value and progress fraction (from 0 to 1), returns the current value. Intended to be used to manage more exotic values like colors.
  * `map_func` - Used to translate the current value to something else, e.g. an angle to a Transform.rotation.

#### EFFECTS
#### `@script slide_color(view, *args, **kwargs)`

  Slide a color value. Supports same
  arguments than slide_value. 

#### `@script hide(view, **kwargs)`

  Fade the view away, then set as hidden 

#### `@script show(view, **kwargs)`

  Unhide view, then fade in. 

#### `@script pulse(view, color='#67cf70')`

  Pulses the background of the view to the given color and back to the original color.
  Default color is a shade of green. 

#### `@script move_to(view, x, y, **kwargs)`

  Move to x, y. 

#### `@script rotate(view, degrees, rps=1, start_value=0, **kwargs)`

  Rotate view given degrees at given rps - rounds per second. Set start_value if not
  starting from 0. 

#### `@script fly_out(view, direction, **kwargs)`

  Moves the view out of the screen in the given direction. Direction is one of the
  following strings: 'up', 'down', 'left', 'right'. 

#### ADDITIONAL EASING FUNCTIONS
#### ` drop_and_bounce(t)`

  Not a script but an easing function simulating something that is dropped and
  bounces a few times. 
