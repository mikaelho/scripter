#coding: utf-8
from scripter import *
from scene import *

class MyScene (Scene):
    
  roll = False
  
  @script # setup can be a script
  def setup(self):
      self.background_color = 'black'
      s = self.ship = SpriteNode('spc:PlayerShip1Orange', alpha=0, scale=2, position=self.size/2, parent=self)
      
      # Animate Scene and the Nodes
      yield 1.0
      pulse(self, 'white')
      s = self.ship
      show(s, duration=2.0)
      scale_to(s, 1, duration=2.0)
      yield
      wobble(s)
      yield
      move_by(s, 0, 100)
      yield
      fly_out(s, 'up')
      yield
      
      l = LabelNode(text='Tap anywhere', position=self.size/2, parent=self)
      reveal_text(l)
      yield 2.0
      hide(l)

  @script # touch events can be scripts
  def touch_began(self, touch):
      target = Vector(touch.location)
      
      if self.roll:
        roll_to(self.ship, target, end_right_side_up=False, duration=1.0)
      else:
        vector = target - self.ship.position
        rotate_to(self.ship, vector.degrees-90)
        yield
        move_to(self.ship, *target, duration=0.7, ease_func=sinusoidal)
        
      self.roll = self.roll == False

run(MyScene())

