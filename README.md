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

# API

* [Class: Scripter](#class-scripter)
  * [Methods](#methods)
  * [Properties](#properties)
* [Class: ScrollingBannerLabel](#class-scrollingbannerlabel)
  * [Methods](#methods)
  * [Properties](#properties)
* [Class: Vector](#class-vector)
  * [Methods](#methods)
  * [Properties](#properties)
* [Functions](#functions)
  * [Script management](#script-management)
  * [Animation primitives](#animation-primitives)
  * [Animation effects](#animation-effects)
  * [Easing functions](#easing-functions)


## Class: Scripter

Class that contains the `update` method used to run the scripts and to control their execution.

Runs at default 60 fps, or not at all when there are no scripts to run.

Inherits from ui.View; constructor takes all the same arguments as ui.View.

## Methods


#### `update(self)`

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

#### `pause_play_all(self)`

  Pause or play all animations. 

#### `cancel(self, script)`

  Cancels any ongoing animations and
  sub-scripts for the given script. 

#### `cancel_all(self)`

  Initializes all internal structures.
  Used at start and to cancel all running scripts.
## Properties


#### `default_update_interval (get)`

  The running rate for the update method. Frames per second is here considered to be just an
  alternative way of setting the update interval, and this property is linked to
  `default_fps` - change one and the other will change as well.

#### `default_fps (get)`

  The running rate for the update method. Frames per second is here considered to be just an
  alternative way of setting the update interval, and this property is linked to
  `default_update_interval` - change one and the other will change as well.
## Class: ScrollingBannerLabel

UI component that scrolls the given text indefinitely, in either direction. Will only scroll if the text is too long to fit into this component.
  

## Methods


#### `__init__(self, **kwargs)`

  In addition to normal `ui.View` arguments, you can include:
    
  * `text` - To be scrolled as a marquee.
  * Label formatting arguments `font` and `text_color`.
  * `initial_delay` - How long we wait before we start scrolling, to enable reading the beginning of the text. Default is 2 seconds.
  * `scrolling_speed` - How fast the text moves, in points per second. Default is 100 pts/s.
  * `to_right` - Set to True if you would like the text to scroll from the left. Default is False.

#### `stop(self)`

  Stops the scrolling and places the text at start. 

#### `restart(self)`

  Restarts the scrolling, including the initial delay, if any. 
## Properties


#### `text (get)`

  You can change the text displayed at
  any point after initialization by setting
  this property. 

# Functions


#### SCRIPT MANAGEMENT
#### `script(func)`

  _Can be used with Scene Nodes._
  
  Decorator for the animation scripts. Scripts can be functions, methods or generators.
  
  First argument of decorated functions must always be the view to be animated.
  
  Calling a script starts the Scripter `update` loop, if not already running.
  
  New scripts suspend the execution of the parent script until all the parallel scripts have
  completed, after which the `update` method will resume the execution of the parent script.

#### `find_scripter_instance(view)`

  _Can be used with Scene Nodes._
  
  Scripts need a "controller" ui.View that runs the update method for them. This function finds 
  or creates the controller for a view as follows:
    
  1. Check if the view itself is a Scripter
  2. Check if any of the subviews is a Scripter
  3. Repeat 1 and 2 up the view hierarchy of superviews
  4. If not found, create an instance of Scripter as a hidden subview of the root view
  
  In case of scene Nodes, search starts from `node.scene.view`.
  
  If you want cancel or pause scripts, and have not explicitly created a Scripter instance to 
  run them, you need to use this method first to find the right one.

#### ANIMATION PRIMITIVES
#### `set_value(view, attribute, value, func=None)`
`@script`

  Generator that sets the `attribute` to a `value` once, or several times if the value itself is a 
  generator or an iterator.
  
  Optional keyword parameters:
  
  * `func` - called with the value, returns the actual value to be set

#### `slide_value(view, attribute, end_value, target=None, start_value=None, duration=None, delta_func=None, ease_func=None, current_func=None, map_func=None, side_func=None)`
`@script`

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

#### `slide_tuple(view, *args, **kwargs)`
`@script`

  Slide a tuple value of arbitrary length. Supports same arguments as `slide_value`. 

#### `slide_color(view, attribute, end_value, **kwargs)`
`@script`

  Slide a color value. Supports the same
  arguments as `slide_value`. 

#### `timer(view, duration=None, action=None)`
`@script`

  Acts as a wait timer for the given duration in seconds. `view` is only used to find the 
  controlling Scripter instance. Optional action function is called every cycle. 

#### ANIMATION EFFECTS
#### `center(view, move_center_to, **kwargs)`
`@script`

  Move view center (anchor for Scene Nodes). 

#### `center_to(view, move_center_to, **kwargs)`
`@script`

  Alias for `center`. 

#### `center_by(view, dx, dy, **kwargs)`
`@script`

  Adjust view center/anchor position by dx, dy. 

#### `expand(view, **kwargs)`
`@script`

  _Not applicable for Scene Nodes._
  
  Expands the view to fill all of its superview. 

#### `fly_out(view, direction, **kwargs)`
`@script`

  Moves the view out of the screen in the given direction. Direction is one of the
  following strings: 'up', 'down', 'left', 'right'. 

#### `hide(view, **kwargs)`
`@script`

  Fade the view away. 

#### `move(view, x, y, **kwargs)`
`@script`

  Move to x, y.
  For UI views, this positions the top-left corner.
  For Scene Nodes, this moves the Node `position`. 

#### `move_to(view, x, y, **kwargs)`
`@script`

  Alias for `move`. 

#### `move_by(view, dx, dy, **kwargs)`
`@script`

  Adjust position by dx, dy. 

#### `pulse(view, color='#67cf70', **kwargs)`
`@script`

  Pulses the background of the view to the given color and back to the original color.
  Default color is a shade of green. 

#### `reveal_text(view, **kwargs)`
`@script`

  Reveals text one letter at a time in the given duration. View must have a `text` attribute. 

#### `roll_to(view, to_center, end_right_side_up=True, **kwargs)`
`@script`

  Roll the view to a target position given by the `to_center` tuple. If `end_right_side_up` is true, view starting angle is adjusted so that the view will end up with 0 rotation at the end, otherwise the view will start as-is, and end in an angle determined by the roll.
  View should be round for the rolling effect to make sense. Imaginary rolling surface is below the view - or to the left if rolling directly downwards. 

#### `rotate(view, degrees, shortest=False, **kwargs)`
`@script`

  Rotate view to an absolute angle. Set start_value if not starting from 0. Positive number rotates clockwise. For UI views, does not mix with other transformations.
  
  Optional arguments:
    
  * `shortest` - If set to True (default), will turn in the "right" direction. For UI views, start_value must be set to a sensible value for this to work.

#### `rotate_to(view, degrees, **kwargs)`

  Alias for `rotate`. 

#### `rotate_by(view, degrees, **kwargs)`
`@script`

  Rotate view by given degrees. 

#### `scale(view, factor, **kwargs)`
`@script`

  Scale view to a given factor in both x and y dimensions. For UI views, you need to explicitly set `start_value` if not starting from 1. 

#### `scale_to(view, factor, **kwargs)`

  Alias for `scale`. 

#### `scale_by(view, factor, **kwargs)`
`@script`

  Scale view relative to current scale factor. 

#### `show(view, **kwargs)`
`@script`

  Slide alpha from 0 to 1. 

#### `wobble(view)`
`@script`

  Little wobble of a view, intended to attract attention. 

#### `wait_for_tap(view)`
`@script`

  Overlays the given view with a temporary transparent view, and
  yields until the view is tapped. 

#### EASING FUNCTIONS
#### `mirror(ease_func, t)`

  Runs the given easing function to the end in half the duration, then backwards in the second half. For example, if the function provided is `linear`, this function creates a "triangle" from 0 to 1, then back to 0; if the function is `ease_in`, the result is more of a "spike".

#### `oscillate(t)`

  Basic sine curve that runs from 0 through 1, 0 and -1, and back to 0. 
