# _SCRIPTER_ - Pythonista UI animation framework

![Logo](https://raw.githubusercontent.com/mikaelho/scripter/master/logo.jpg)

# Quick start

In order to start using the animation effects, just import scripter and use the effects like this:

    from scripter import *
    
    hide(my_button)
    
All effects expect an active UI view as the first argument.

If you want to create a more complex animation from the effects provided, combine them in a
script:
  
    @script
    def my_script():
      move_to(my_button, 50, 200)
      pulse(my_button, 'red')
      yield
      hide(my_button)
      
Here movement and a red highlight happen at the same time. After both actions are completed, `my_button` fades away.

If you want 'built-in' animations in your custom ui.View, you can inherit from Scripter instead, as it inherits from ui.View:
  
    class MyView(Scripter):
      
      @script
      def my_script(self):
        self.move_to(50, 200)
        self.pulse('red')
        yield
        self.hide()
        
See the API documentation for individual effects and how to roll your own with `set_value`, `slide_value` and `timer`.

_Note_: As of Sep 15, 2017, ui.View.update is only available in Pythonista 3 beta.

# Classes

## Scripter

Class that contains the update method used to run the scripts and to control their execution
order.

Runs at default 60 fps, or not at all when there are no scripts to run.

Inherits from ui.View; constructor takes all the same arguments as ui.View.


  * `default_update_interval(self)`


  * `default_update_interval(self, value)`


  * `default_fps(self)`


  * `default_fps(self, value)`


  * `update(self)`

  Run active steppers, remove finished ones,
  activate next steppers. 

  * `pause_play_all(self)`

  Pause or play all animations. 

  * `cancel(self, script)`

  Cancels any ongoing animations and
  sub-scripts for the given script. 

  * `cancel_all(self)`

  Initializes all internal structures.
  Used at start and to cancel all running scripts.
# Functions


  * `script(func)`

  Decorator for the animation scripts. Scripts can be functions, methods or generators.
  
  First argument of decorated functions must always be the view to be animated.

  * `find_scripter_instance(view)`

  Scripts need a "controller" ui.View that runs the update method for them. This function finds or creates the controller for a view as follows:
    * Check if the view itself is a Scripter
    * Check if any of the subviews is a Scripter
    * Repeat up the view hierarchy of superviews
    * If not found, create as a hidden subview of the root view
  
  If you want cancel or pause scripts, and have not explicitly created a Scripter instance to 
  run then, you need to use this method first to find the right one.

  * `timer(view, duration, action=None)`

  Acts as a wait timer. Optional action is
  called every cycle. 

  * `set_value(view, attribute, value, func=None)`

  Generator that sets the `attribute` to a 
  `value` once, or several times if the value 
  itself is a generator.
  
  Optional keyword parameters:
    * `func` - called with the value, returns the actual value to be set
    * `target` - object whose attribute is to be set. If not given, `self` is used. 

  * `slide_value(view, attribute, end_value, target=None, start_value=None, duration=None, delta_func=None, ease_func=None, current_func=None, map_func=None)`

  Generator that "slides" the `value` of an
  `attribute` to an `end_value` in a given duration.
  
  Optional keyword parameters:
    * `target` - object whose attribute is to be set. If not given, `self` is used.
    * `start_value` - set if you want some other value than the current value of the attribute as the animation start value.
    * `duration` - time it takes to change to the target value. Default is 0.5 seconds.
    * `delta_func` - use to transform the range from start_value to end_value to something else.
    * `ease_func` - provide to change delta-t value to something else. Mostly used for easing; you can provide an easing function name as a string instead of an actual function. See supported easing functions [here](https://raw.githubusercontent.com/mikaelho/scripter/master/ease-functions.png).
    * `current_func` - Given the start value, delta value and progress fraction (from 0 to 1), returns the current value. Intended to be used to manage more exotic values like colors.
    * `map_func` - Used to translate the current value to something else, e.g. an angle to a Transform.rotation.

  * `slide_color(view, *args, **kwargs)`

  Slide a color value. Supports same
  arguments than slide_value. 

  * `hide(view, **kwargs)`

  Fade the view away, then set as hidden 

  * `show(view, **kwargs)`

  Unhide view, then fade in. 

  * `pulse(view, color='#67cf70')`


  * `move_to(view, x, y, **kwargs)`

  Move to x, y 

  * `rotate(view, degrees, rps=1, start_value=0, **kwargs)`

  Rotate view given degrees at given rps - rounds per second. Set start_value if not
  starting from 0. 

  * `fly_out(view, direction, **kwargs)`


  * `drop_and_bounce(t)`

  Not a script but an easing function simulating something that is dropped and
  bounces a few times. 
