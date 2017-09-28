#coding: utf-8
from functools import partial
import math

from ui import *
import dialogs

from scripter import *

class DemoView(View):
  
  def __init__(self):
    self.start_point = (200,400)
    self.axes_counter = 150
    self.curve_point_x = None
    self.curve_point_y = None
    self.curve = []
    self.start_new = False
  
  def draw(self):
    
    spx = self.start_point[0]
    spy = self.start_point[1]
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
    
    if self.start_new:
      self.curve = []
      self.start_new = False
      
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

if __name__ == '__main__':
  
  effect_duration = 0.5
  ease_function = linear
  
  v = DemoView()
  v.background_color = 'white'
  v.present('full_screen')

  d = View(frame=(0,0,10,10), corner_radius=5, background_color='black')
  d.center = (200,400)
  v.add_subview(d)

  l = Label(text='Demo', hidden=True, alignment=ALIGN_CENTER, frame=(100, -100, 75, 40), corner_radius=10)
  v.add_subview(l)

  @script
  def demo_action(view, demo_func, sender):
    demo_func(view)
    slide_value(d, 'x', d.x+140, duration=effect_duration)
    slide_value(d, 'y', d.y-140, ease_func=ease_function, duration=effect_duration)
    yield 2 # sec delay before restoring state
    initial_state()
    
  def initial_state():
    slide_tuple(l, 'frame', (100, 380, 75, 40))
    l.hidden = False
    l.alpha = 1.0
    l.transform = Transform.rotation(0)
    l.font = ('<system>', 16)
    slide_color(l, 'background_color', 'transparent')
    slide_value(d, 'center', (200,400))

  initial_state()

  @script
  def demo_hide(view):
    hide(l, duration=effect_duration)

  @script
  def demo_move(view):
    move(l, 100, 240, duration=effect_duration, ease_func=ease_function)
    
  @script
  def demo_pulse(view):
    pulse(l)
    
  def demo_rotate(view):
    rotate(l, 360, duration=effect_duration, ease_func=ease_function)
    
  def demo_scale(view):
    scale(l, 3, duration=effect_duration, ease_func=ease_function)
    
  def demo_fly_out(view):
    fly_out(l, 'down', duration=effect_duration, ease_func=ease_function)

  def demo_expand(view):
    l.background_color = 'grey'
    expand(l, duration=effect_duration, ease_func=ease_function)
    
  def demo_font_size(view):
    def size_but_keep_centered():
      cntr = l.center
      l.size_to_fit()
      l.center = cntr
      
    slide_value(l, 'font', 64, start_value=l.font[1], map_func=lambda v: ('<system>', v), duration=effect_duration, ease_func=ease_function, side_func=size_but_keep_centered)

  demos = [
    ('Hide',),
    ('Move',),
    ('Pulse',),
    ('Rotate',),
    ('Scale',),
    ('Fly out',),
    ('Expand',),
    ('Font size',)
  ]
  
  preset_durations = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]
  
  duration_label = Label(text='0.5 seconds', frame=(20,20,150,20), alignment=ALIGN_CENTER)
  duration_slider = Slider(frame=(20,45,150,20), continuous=True, value=0.1)
  v.add_subview(duration_label)
  v.add_subview(duration_slider)
  
  def slider_action(sender):
    global effect_duration
    slot = round(sender.value*(len(preset_durations)-1))
    effect_duration = preset_durations[slot]
    duration_label.text = str(effect_duration) + ' seconds'
    
  duration_slider.action = slider_action
  
  ease_funcs = [ linear, sinusoidal, ease_in, ease_out, ease_in_out, elastic_out, elastic_in,  elastic_in_out, bounce_out, bounce_in, bounce_in_out, ease_back_in, ease_back_out, ease_back_in_out ]
  
  ease_label = Label(text='linear', frame=(200, 20, 150, 40), touch_enabled=True, corner_radius=7, border_color='black', border_width=2, alignment=ALIGN_CENTER)
  ease_click = Button(frame=(0, 0, 150, 40), flex='WH')
  ease_label.add_subview(ease_click)
  
  def ease_action(sender):
    global ease_function
    selection = dialogs.list_dialog('Select easing function', [ func.__name__ for func in ease_funcs])
    if selection:
      ease_label.text = selection
      ease_function = globals()[selection]
      draw_ease(v)
  
  @script    
  def draw_ease(view):
    v.start_new = True
    slide_value(v, 'curve_point_x', 140, start_value=1, duration=0.7)
    slide_value(v, 'curve_point_y', 140, start_value=1, ease_func=ease_function, map_func=v.trigger_refresh, duration=0.7)
    
  draw_ease(v)
  
  ease_click.action = ease_action

  v.add_subview(ease_label)
  
  buttons_per_line = math.floor((v.width-40)/85)
  for i, (demo_name, ) in enumerate(demos):
    line = math.floor(i/buttons_per_line)
    column = i - line*buttons_per_line
    demo_btn = Button(title=demo_name, corner_radius=7)
    demo_btn.frame = (20 + column*85, 85+line*50, 75, 40)
    demo_btn.background_color = 'black'
    demo_btn.tint_color = 'white'
    demo_func_name = ('demo_'+demo_name).replace(' ', '_').lower()
    demo_btn.action = partial(demo_action, v, globals()[demo_func_name])
    v.add_subview(demo_btn)
