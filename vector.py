# coding: utf-8
import math

class Vector (list):
  ''' Simple 2D vector class to make vector operations more convenient. If performance is a concern, you are probably better off looking at numpy.
  
  Supports the following operations:
    
  * Initialization from two arguments, two keyword  arguments (`x` and `y`), tuple, list, or another Vector.
  * Equality and unequality comparisons to other vectors. For floating point numbers, equality tolerance is 1e-10.
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
      
      assert list(Vector(1, 1).steps_to(Vector(3, 3))) == [[1.7071067811865475, 1.7071067811865475], [2.414213562373095, 2.414213562373095], [3, 3]]
      assert list(Vector(1, 1).steps_to(Vector(-1, 1))) == [[0, 1], [-1, 1]]
      assert list(Vector(1, 1).rounded_steps_to(Vector(3, 3))) == [[2, 2], [2, 2], [3, 3]]
  '''

  abs_tol = 1e-10

  def __init__(self, *args, **kwargs):    
    if len(args) + len(kwargs) == 0:
      self.append(0)
      self.append(0)
    else:
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

  def projection_to(self, other):
    ''' Vector projection of this vector to another vector. '''
    result_vector = Vector(other)
    scale_factor = other.dot_product(self)/(other.magnitude**2)
    result_vector.magnitude *= scale_factor
    return result_vector
    
  def rejection_from(self, other):
    ''' The perpendicular vector that remains when we take out the projected component. '''
    return self - self.projection_to(other)

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
    ''' As `steps_to`, but returns unique points rounded to the nearest integer. '''
    previous = Vector(0,0)
    for step in self.steps_to(other, step_magnitude):
      rounded = round(step)
      if rounded != previous:
        previous = rounded
        yield rounded
    

if __name__ == '__main__':
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
  
  assert list(Vector(1, 1).steps_to(Vector(3, 3))) == [[1.7071067811865475, 1.7071067811865475], [2.414213562373095, 2.414213562373095], [3, 3]]
  assert list(Vector(1, 1).steps_to(Vector(-1, 1))) == [[0, 1], [-1, 1]]
  assert list(Vector(1, 1).rounded_steps_to(Vector(3, 3))) == [[2, 2], [3, 3]]
  
  v4 = Vector(0,1)
  v5 = Vector(5,5)
  assert v4.projection_to(v5) == (0.5, 0.5)
  assert v4.rejection_from(v5) == (-0.5, 0.5)
