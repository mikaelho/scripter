# coding: utf-8
import math

class Vector (list):

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
    return self[0]

  @x.setter
  def x(self, value):
    self[0] = value

  @property
  def y(self):
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
    return self.x * other.x + self.y * other.y

  def distance_to(self, other):
    return (Vector(other) - self).magnitude

  @property
  def magnitude(self):
    return math.hypot(self.x, self.y)

  @magnitude.setter
  def magnitude(self, m):
    r = self.radians
    self.polar(r, m)

  @property
  def radians(self):
    #return round(math.atan2(self.y, self.x), 10)
    return math.atan2(self.y, self.x)

  @radians.setter
  def radians(self, r):
    m = self.magnitude
    self.polar(r, m)

  def polar(self, r, m):
    self.y = math.sin(r) * m
    self.x = math.cos(r) * m
    
  @property
  def degrees(self):
    return math.degrees(self.radians)

  @degrees.setter
  def degrees(self, d):
    self.radians = math.radians(d)
    
  def steps_to(self, other, step_magnitude=1.0):
    """ Generator that returns points on the line between this and the other point. Does not include the starting point. """
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
    for step in self.steps_to(other):
      yield round(step)
    

if __name__ == '__main__':
  v = Vector(x = 1, y = 2)
  v2 = Vector(3,4)
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
  
  assert list(Vector(1, 1).steps_to(Vector(3, 3))) == [[1.7071067811865475, 1.7071067811865475], [2.414213562373095, 2.414213562373095], [3, 3]]
  assert list(Vector(1, 1).steps_to(Vector(-1, 1))) == [[0, 1], [-1, 1]]
  assert list(Vector(1, 1).rounded_steps_to(Vector(3, 3))) == [[2, 2], [2, 2], [3, 3]]

