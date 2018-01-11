#coding: utf-8
from functools import partial
from random import random
import math, inspect

from ui import *
import dialogs

from scripter import *

class DemoView(View):
  
  def __init__(self):
    self.start_point = (200,175)
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
  
  cleaner = None
  color_changer = None
  
  graph_start = 175
  options_start = 210
  buttons_start = 270
  
  v = DemoView()
  v.background_color = 'white'
  v.present('full_screen')

  d = View(frame=(0,0,10,10), corner_radius=5, background_color='black')
  d.center = (200,graph_start)
  v.add_subview(d)

  c = TextView(flex='WH', editable=False)
  v.add_subview(c)

  demo_label = Label(text='Demo', hidden=True, alignment=ALIGN_CENTER, frame=(100, -100, 75, 40), corner_radius=10)
  v.add_subview(demo_label)

  @script
  def demo_action(view, demo_func, animate_ease, sender):
    global cleaner
    if cleaner:
      find_scripter_instance(view).cancel(cleaner)
    demo_func(view)
    if animate_ease:
      slide_value(d, 'x', d.x+140, duration=effect_duration)
      slide_value(d, 'y', d.y-140, ease_func=ease_function, duration=effect_duration)
    code = inspect.getsource(demo_func)
    code = code.replace('ease_function', ease_function.__name__)
    code = code.replace('effect_duration', str(effect_duration))
    lines = code.splitlines()
    code = '\n'.join(lines[2:])
    c.text = code
    cleaner = clean_up(view, effect_duration+2)
    #yield 2 # sec delay before restoring state
    #initial_state()
  
  @script  
  def clean_up(view, delay):
    global cleaner
    yield delay
    cleaner = None
    initial_state()
    
  def initial_state():
    global graph_start, color_changer
    demo_label.text = 'Demo'
    slide_tuple(demo_label, 'center', (100+75/2, graph_start))
    slide_value(demo_label, 'width', 75)
    slide_value(demo_label, 'height', 40)
    demo_label.hidden = False
    demo_label.alpha = 1.0
    demo_label.transform = Transform.rotation(0)
    demo_label.font = ('<system>', 16)
    if not color_changer:
      slide_color(demo_label, 'background_color', 'transparent')
    slide_value(d, 'center', (200, graph_start))

  @script
  def demo_move(view):
    move(view, 100, view.y-140, duration=effect_duration, ease_func=ease_function)
    
  @script
  def demo_move_by(view):
    facets = 36
    
    vct = Vector(0, facets/2)
    
    for _ in range(facets):
      move_by(view, vct.x, vct.y, duration=effect_duration/facets, ease_func=ease_function)
      yield
      vct.degrees -= 360/facets
    
  @script
  def demo_hide_and_show(view):
    hide(view, duration=effect_duration, ease_func=ease_function)
    yield
    show(view, duration=effect_duration, ease_func=ease_function)
    
  @script
  def demo_pulse(view):
    pulse(view, duration=effect_duration, ease_func=ease_function)
    
  @script
  def demo_roll_to(view):
    cx, cy = view.center
    roll_to(view, (cx, cy-140), duration=effect_duration, ease_func=ease_function)
    
  @script
  def demo_rotate(view):
    rotate(view, 360, duration=effect_duration, ease_func=ease_function)
   
  @script 
  def demo_rotate_by(view):
    for _ in range(4):
      rotate_by(view, 90, duration=effect_duration/4, ease_func=ease_function)
      yield
    
  @script
  def demo_scale(view):
    scale(view, 3, duration=effect_duration, ease_func=ease_function)
  
  @script  
  def demo_scale_by(view):
    for _ in range(3):
      scale_by(view, 2, duration=effect_duration/3, ease_func=ease_function)
      yield
    
  @script
  def demo_fly_out(view):
    fly_out(view, 'down', duration=effect_duration, ease_func=ease_function)

  @script
  def demo_expand(view):
    view.background_color = 'grey'
    expand(view, duration=effect_duration, ease_func=ease_function)
  
  @script
  def demo_count(view):
    set_value(view, 'text', range(1, 101), str)
    
  @script
  def demo_wobble(view):
    wobble(view)
    
  @script
  def demo_font_size(view):
    def size_but_keep_centered():
      cntr = view.center
      view.size_to_fit()
      view.center = cntr
      
    slide_value(view, 'font', 128, start_value=view.font[1], map_func=lambda font_size: ('<system>', font_size), duration=effect_duration, ease_func=ease_function, side_func=size_but_keep_centered)
    
  @script
  def demo_colors(view):    
    global color_changer
    @script
    def change_color_forever(view):
      while True:
        random_color = (random(), random(), random(), 1.0)
        slide_color(view, 'background_color', random_color, duration=effect_duration)
        yield

    if color_changer:
      find_scripter_instance(view).cancel(color_changer)
      color_changer = None
      v['demo_colors'].background_color = 'black'
    else:
      color_changer = change_color_forever(view)
      v['demo_colors'].background_color = 'red'
  
  @script
  def demo_reveal_text(view):
    reveal_text(duration_label, duration=effect_duration, ease_func=ease_function)

  demos = [
    ('Move', True),
    ('Move by', False),
    ('Hide and show', False),
    ('Pulse', False),
    ('Expand', True),
    ('Count', False),
    ('Roll to', True),
    ('Rotate', True),
    ('Rotate by', False),
    ('Scale', True),
    ('Scale by', False),
    ('Font size', True),
    ('Fly out', True),
    ('Wobble', False),
    ('Colors', False),
    ('Reveal text', True),
  ]
  
  @script
  def demo_all(view):
    for demo_name, animate_ease in demos:
      func_name = create_func_name(demo_name)
      v[func_name].background_color = '#c25a5a'
      globals()[func_name](demo_label)
      if animate_ease:
        slide_value(d, 'x', d.x+140, duration=effect_duration)
        slide_value(d, 'y', d.y-140, ease_func=ease_function, duration=effect_duration)
      yield
      initial_state()
      v[func_name].background_color = 'black'
      yield
  
  button_width = 90
  button_height = 25
  gap = 5
  width_gap = button_width + gap
  height_gap = button_height + gap
  buttons_per_line = math.floor((v.width-40)/width_gap)
  lines = (len(demos)+1)/buttons_per_line
  total_height = lines * height_gap
  
  cy = buttons_start + total_height + 20
  
  scroll_label = ScrollingBannerLabel(
    text='Use this tool to experiment with the various scripter animation effects as well as the impact that changing the effect duration or ease function has. All effects are applied to the "Demo" label above. Select different ease functions to see them illustrated as a graph; the basic "Move" effect is probably the best starting point to understand ease functions. Launching several effects in quick succession will lead to unpredictable results. Code for each effect launched is displayed under this text for your copy-paste convenience in case you want to use the effect. This scrolling text demonstrates the specialized ScrollingBannerLabel component. ***'
  )
  scroll_label.frame = (20, cy, v.width-40, 30)
  v.add_subview(scroll_label)
  
  c.frame = (20, cy+30, v.width-40, v.height-cy-50)
  
  initial_state()
  
  preset_durations = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 7.0, 10.0]
  
  duration_label = Label(text='0.5 seconds', frame=(20,options_start,150,20), alignment=ALIGN_LEFT)
  duration_slider = Slider(frame=(20,options_start+25,150,20), continuous=True, value=0.1)
  v.add_subview(duration_label)
  v.add_subview(duration_slider)
  
  def slider_action(sender):
    global effect_duration
    slot = round(sender.value*(len(preset_durations)-1))
    effect_duration = preset_durations[slot]
    duration_label.text = str(effect_duration) + ' seconds'
    
  duration_slider.action = slider_action
  
  ease_funcs = [ linear, sinusoidal, ease_in, ease_out, ease_in_out, ease_out_in, elastic_out, elastic_in,  elastic_in_out, bounce_out, bounce_in, bounce_in_out, ease_back_in, ease_back_in_alt, ease_back_out, ease_back_out_alt, ease_back_in_out, ease_back_in_out_alt ]
  
  ease_label = Label(text='linear', frame=(200, options_start, 150, 40), touch_enabled=True, corner_radius=7, border_color='black', border_width=2, alignment=ALIGN_CENTER)
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
  
  def create_button(title, action):
    demo_btn = Button(title=title, corner_radius=7)
    demo_btn.background_color = 'black'
    demo_btn.tint_color = 'white'
    demo_btn.action = action
    demo_btn.font = ('<System>', 12)
    demo_btn.width, demo_btn.height = (button_width, button_height)
    return demo_btn
    
  def create_func_name(demo_name):
    return ('demo_'+demo_name).replace(' ', '_').lower()
  
  all_btn = create_button('All', demo_all)
  all_btn.x, all_btn.y = (20, buttons_start)
  all_btn.background_color = '#666666'
  v.add_subview(all_btn)
  
  for j, (demo_name, animate_ease) in enumerate(demos):
    i = j+1
    line = math.floor(i/buttons_per_line)
    column = i - line*buttons_per_line
    demo_func_name = create_func_name(demo_name)
    action = partial(demo_action, demo_label, globals()[demo_func_name], animate_ease)
    btn = create_button(demo_name, action)
    btn.name = demo_func_name
    btn.x, btn.y = (20 + column*width_gap, buttons_start+line*height_gap)
    v.add_subview(btn)
