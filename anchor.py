
import json
import math
import re
import textwrap

from scripter import *


_anchor_rules_spec = """
left:
    type: leading
    target:
        attribute: target.x
        same: value
        different: value + gap
        flex: width
    source:
        regular: source.x
        container: source.bounds.x
right:
    type: trailing
    target:
        attribute: target.x
        same: value - target.width
        different: value - target.width - gap
        flex: width
    source:
        regular: source.frame.max_x
        container: source.bounds.max_x
top:
    type: leading
    target:
        attribute: target.y
        same: value
        different: value + gap
        flex: height
    source:
        regular: source.y
        container: source.bounds.y
bottom:
    type: trailing
    target:
        attribute: target.y
        same: value - target.height
        different: value - target.height - gap
        flex: height
    source:
        regular: source.frame.max_y
        container: source.bounds.max_y
center_x:
    type: neutral
    target:
        attribute: target.x
        same: value - target.width / 2
    source:
        regular: source.center.x
        container: source.bounds.center().x
center_y:
    type: neutral
    target:
        attribute: target.y
        same: value - target.height / 2
    source:
        regular: source.center.y
        container: source.bounds.center().y
center:
    type: neutral
    target:
        attribute: target.center
        same: value
    source:
        regular: source.center
        container: source.bounds.center()
width:
    type: neutral
    target:
        attribute: target.width
        same: value
    source:
        regular: source.width
        container: source.bounds.width - 2 * gap
height:
    type: neutral
    target:
        attribute: target.height
        same: value
    source:
        regular: source.height
        container: source.height - 2 * gap
heading:
    type: neutral
    target:
        attribute: target._scripter_at._heading
        same: direction(target, source, value)
    source:
        regular: source._scripter_at._heading
        container: source._scripter_at._heading
"""

template = """
attr:
    type: 
    target:
        attribute: 
        same: 
        different: 
        flex: 
    source:
        regular: 
        container: 
"""


class At:
    
    gap = 8  # Apple Standard gap
    
    class Anchor:
        
        REGULAR, CONTAINER = 'regular', 'container'
        
        SAME, DIFFERENT, NEUTRAL = 'same', 'different', 'neutral'
        
        TRAILING, LEADING = 'trailing', 'leading'
        
        def __init__(self, source_at, source_prop):
            self.source_at = source_at
            self.source_prop = source_prop
            self.modifiers = ''
            
        def set_target(self, target_at, target_prop):
            self.target_at = target_at
            self.target_prop = target_prop
            self.type = (
                self.CONTAINER
                if target_at.view.superview == self.source_at.view
                else self.REGULAR
            )
            source_type = _rules[self.source_prop]['type']
            target_type = _rules[self.target_prop]['type']
            
            #print(source_type, target_type)
            
            self.same = self.SAME if any([
                source_type == self.NEUTRAL,
                target_type == self.NEUTRAL,
                source_type == target_type,
            ]) else self.DIFFERENT
            
            #print(self.same)
            
            if (self.type == self.CONTAINER and
            self.NEUTRAL not in (source_type, target_type)):
                self.same = self.SAME if self.same == self.DIFFERENT else self.DIFFERENT
                
            
        def start_script(self):
            source_value = _rules[self.source_prop]['source'][self.type]
            target_value = _rules[self.target_prop]['target'][self.same]
            target_attribute = _rules[self.target_prop]['target']['attribute']
            
            previous_runner = self.target_at.running_scripts.pop(
                self.target_prop, None)
            if previous_runner:
                cancel(previous_runner)
            
            script_str = (
                f'''\
                @script  #(run_last=True)
                def anchor_runner(source, target):
                    gap = {At.gap}
                    while True:
                        value = {source_value} {self.modifiers}
                        target_value = {target_value}
                        if {target_attribute} != target_value:
                            {target_attribute} = target_value
                        yield
                        
                self.target_at.running_scripts[self.target_prop] = \
                    anchor_runner(self.source_at.view, self.target_at.view)
                '''
            )
            
            exec(textwrap.dedent(script_str))
            
        def __add__(self, other):
            self.modifiers += f'+ {other}'
            return self
            
        def __sub__(self, other):
            self.modifiers += f'- {other}'
            return self
            
        def __mul__(self, other):
            self.modifiers += f'* {other}'
            return self
            
        def __div__(self, other):
            self.modifiers += f'/ {other}'
            return self
            
        def __mod__(self, other):
            self.modifiers += f'% {other}'
            return self
            
        def __pow__ (self, other, modulo=None):
            self.modifiers += f'** {other}'
            return self
    
    def __new__(cls, view):
        try:
            return view._scripter_at
        except AttributeError:
            at = super().__new__(cls)
            at.view = view
            at.__heading = 0
            at.heading_adjustment = 0
            at.running_scripts = {}
            view._scripter_at = at
            return at

    def _prop(attribute, flex=False):
        p = property(
            lambda self:
                partial(At._getter, self, attribute)(),
            lambda self, value:
                partial(At._setter, self, attribute, flex, value)()
        )
        return p

    def _getter(self, attr_string):
        return At.Anchor(self, attr_string)

    def _setter(self, attr_string, flex, value):
        source_anchor = value
        source_anchor.set_target(self, attr_string)
        source_anchor.flex = flex
        source_anchor.start_script()
            
    # ---------------- PROPERTIES
            
    left = _prop('left')
    right = _prop('right')
    top = _prop('top')
    bottom = _prop('bottom')
    
    left_flex = _prop('left', True)
    right_flex = _prop('right', True)
    top_flex = _prop('top', True)
    bottom_flex = _prop('bottom', True)
    
    center = _prop('center')
    center_x = _prop('center_x')
    center_y = _prop('center_y')
    width = _prop('width')
    height = _prop('height')
    heading = _prop('heading')
    
    
    @property
    def _heading(self):
        return self.__heading
        
    @_heading.setter
    def _heading(self, value):
        self.__heading = value
        self.view.transform = ui.Transform.rotation(
            value + self.heading_adjustment)
        
    
# Helper functions
    

    
def direction(target, source, value):
    """
    Calculate the heading if given a center
    """
    try:
        if len(value) == 2:
            source_center = ui.convert_point(value, source.superview)
            target_center = ui.convert_point(target.center, target.superview)
            delta = source_center - target_center
            value = math.atan2(delta.y, delta.x)
    except TypeError:
        pass
    return value
    

def _parse_rules(rules):    
    rule_dict = dict()
    dicts = [rule_dict]
    spaces = re.compile(' *')
    for i, line in enumerate(rules.splitlines()):
        i += 11  # Used to match error line number to my file
        if line.strip() == '': continue
        indent = len(spaces.match(line).group())
        if indent % 4 != 0:
            raise RuntimeError(f'Broken indent on line {i}')
        indent = indent // 4 + 1
        if indent > len(dicts):
            raise RuntimeError(f'Extra indentation on line {i}')
        dicts = dicts[:indent]
        line = line.strip()
        if line.endswith(':'):
            key = line[:-1].strip()
            new_dict = dict()
            dicts[-1][key] = new_dict
            dicts.append(new_dict)
        else:
            try:
                key, content = line.split(':')
                dicts[-1][key.strip()] = content.strip()
            except Exception as error:
                raise RuntimeError(f'Cannot parse line {i}', error)
    return rule_dict
    
_rules = _parse_rules(_anchor_rules_spec)

    
if __name__ == '__main__':
    
    import time
    import ui
    
    class Marker(ui.View):
        
        def __init__(self, superview, radius=15, background_color='grey'):
            super().__init__(
                background_color=background_color
            )
            self._prev_size = self.width
            self.radius = radius
            superview.add_subview(self)
            
        def layout(self):
            if self.width != self._prev_size:
                dim = self.width
            else:
                dim = self.height
            self.height = self.width = dim
            self.corner_radius = self.width/2
        
        @property
        def radius(self):
            return self.width / 2
            
        @radius.setter
        def radius(self, value):
            self.width = value * 2
            
    class Mover(Marker):
        
        def touch_moved(self, t):
            self.center += t.location - t.prev_location
    
    v = ui.View(
        background_color='black',
    )
    set_scripter_view(v)
    
    menu_view = ui.Label(
        text='MENU',
        text_color='white',
        alignment=ui.ALIGN_CENTER,
        border_color='white',
        border_width=1,
        background_color='grey',
        frame=v.bounds,
        width=300,
        flex='H'
    )
    
    main_view = ui.Label(
        text='',
        text_color='white',
        alignment=ui.ALIGN_RIGHT,
        border_color='white',
        border_width=1,
        #background_color='red',
        frame=v.bounds,
        flex='WH',
        touch_enabled=True,
    )
    
    v.add_subview(menu_view)
    v.add_subview(main_view)
    
    def open_and_close(sender):
        
        x(
            main_view, 
            0 if main_view.x > 0 else menu_view.width, 
            ease_func=ease_in_out,
            duration=1,
        )
    
    menu_button = ui.Button(
        image=ui.Image('iow:drag_32'),
        tint_color='white',
        action=open_and_close)
        
    main_view.add_subview(menu_button)
    
    At(menu_button).left = At(main_view).left
    At(menu_button).top = At(main_view).top

    At(menu_view).right = At(main_view).left
    
    m1 = Marker(main_view)
    At(m1).top = At(main_view).top + 100
    At(m1).center_x = At(main_view).center_x
    
    bottom_bar = ui.View(
        background_color='grey'
    )
    main_view.add_subview(bottom_bar)

    bb = At(bottom_bar)
    mv = At(main_view)
    bb.width = mv.width
    bb.bottom = mv.bottom
    bb.left = mv.left
    
    pointer = ui.ImageView(image=ui.Image('iow:ios7_arrow_thin_down_32'))
    main_view.add_subview(pointer)
    At(pointer).heading_adjustment = - math.pi / 2
    At(pointer).center = mv.center
    
    mover = Mover(
        main_view,
        background_color='darkred')
        
    mover.center = (100,100)
    At(pointer).heading = At(mover).center
    
    v.present('fullscreen', 
        animated=False
    )
