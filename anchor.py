
import json
import math
import re
import textwrap

from functools import partialmethod, partial

import ui

from scripter import *


_anchor_rules_spec = """
left:
    type: leading
    target:
        attribute: target.x
        value: value
    source:
        regular: source.x
        container: source.bounds.x
        safe: safe.origin.x
right:
    type: trailing
    target:
        attribute: target.x
        value: value - target.width
    source:
        regular: source.frame.max_x
        container: source.bounds.max_x
        safe: safe.origin.x + safe.size.width
top:
    type: leading
    target:
        attribute: target.y
        value: value
    source:
        regular: source.y
        container: source.bounds.y
        safe: safe.origin.y
bottom:
    type: trailing
    target:
        attribute: target.y
        value: value - target.height
    source:
        regular: source.frame.max_y
        container: source.bounds.max_y
        safe: safe.origin.y + safe.size.height
left_flex:
    type: leading
    target:
        attribute: (target.x, target.width)
        value: (value, target.width - (value - target.x))
right_flex:
    type: trailing
    target:
        attribute: target.width
        value: target.width + (value - (target.x + target.width))
top_flex:
    type: leading
    target:
        attribute: (target.y, target.height)
        value: (value, target.height - (value - target.y))
bottom_flex:
    type: trailing
    target:
        attribute: target.height
        value: target.height + (value - (target.y + target.height))
center_x:
    type: neutral
    target:
        attribute: target.x
        value: value - target.width / 2
    source:
        regular: source.center.x
        container: source.bounds.center().x
        safe: source.bounds.center().x
center_y:
    type: neutral
    target:
        attribute: target.y
        value: value - target.height / 2
    source:
        regular: source.center.y
        container: source.bounds.center().y
        safe: source.bounds.center().y
center:
    type: neutral
    target:
        attribute: target.center
        value: value
    source:
        regular: source.center
        container: source.bounds.center()
        safe: source.bounds.center()
width:
    type: neutral
    target:
        attribute: target.width
        value: value
    source:
        regular: source.width
        container: source.bounds.width - 2 * border_gap
        safe: safe.size.width - 2 * border_gap
height:
    type: neutral
    target:
        attribute: target.height
        value: value
    source:
        regular: source.height
        container: source.bounds.height - 2 * border_gap
        safe: safe.size.height - 2 * border_gap
heading:
    type: neutral
    target:
        attribute: target._scripter_at._heading
        value: direction(target, source, value)
    source:
        regular: source._scripter_at._heading
        container: source._scripter_at._heading
        safe: source._scripter_at._heading
"""


class At:
    
    gap = 8  # Apple Standard gap
    safe = True  # Avoid iOS UI elements
    TIGHT = -gap
    
    class Anchor:
        
        REGULAR, CONTAINER, SAFE = 'regular', 'container', 'safe'
        
        SAME, DIFFERENT, NEUTRAL = 'same', 'different', 'neutral'
        
        TRAILING, LEADING = 'trailing', 'leading'
        
        def __init__(self, source_at, source_prop):
            self.source_at = source_at
            self.source_prop = source_prop
            self.modifiers = ''
            
        def set_target(self, target_at, target_prop):
            self.target_at = target_at
            self.target_prop = target_prop
            
            if target_at.view.superview == self.source_at.view:
                if At.safe:
                    self.type = self.SAFE
                else:
                    self.type = self.CONTAINER
            else:
                self.type = self.REGULAR
            
            source_type = _rules[self.source_prop]['type']
            target_type = _rules[self.target_prop]['type']
            
            #print(source_type, target_type)
            
            self.same = self.SAME if any([
                source_type == self.NEUTRAL,
                target_type == self.NEUTRAL,
                source_type == target_type,
            ]) else self.DIFFERENT
            
            #print(self.same)
            
            if (self.type in (self.CONTAINER, self.SAFE) and
            self.NEUTRAL not in (source_type, target_type)):
                self.same = self.SAME if self.same == self.DIFFERENT else self.DIFFERENT
                
            self.effective_gap = ''
            if self.same == self.DIFFERENT:
                self.effective_gap = (
                    f'+ {At.gap}' if target_type == self.LEADING
                    else f'- {At.gap}')              
            
        def start_script(self):
            self.target_at._remove_anchor(self.target_prop)
            
            update_code = self.get_update_code()
            
            script_str = (
                f'''\
                # {self.target_prop}
                @script  #(run_last=True)
                def anchor_runner(source, target, scripts):
                    while True: {update_code}
                        
                self.target_at.running_scripts[self.target_prop] = \
                    anchor_runner(
                        self.source_at.view, 
                        self.target_at.view,
                        self.target_at.running_scripts)
                '''
            )
            run_script = textwrap.dedent(script_str)
            
            #print(self.target_prop, self.get_opposite())
            #if self.target_prop == 'left':
            #    print(run_script)
            
            exec(run_script)
            
        def get_update_code(self):
            source_prop = self.source_prop
            target_prop = self.target_prop
            opposite_prop = self.get_opposite(target_prop)
            
            if opposite_prop:
                flex_prop = f'{target_prop}_flex'
                return f'''
                        if '{opposite_prop}' in scripts:
                            {self.get_code(source_prop, flex_prop)}
                        else:{self.get_code(source_prop, target_prop)}'''
            else:
                return self.get_code(source_prop, target_prop)
            
        def get_code(self, source_prop, target_prop):
            source_value = _rules[source_prop]['source'][self.type]
            target_value = _rules[target_prop]['target']['value']
            target_attribute = _rules[target_prop]['target']['attribute']
            
            source_value = source_value.replace('border_gap', str(At.gap))
            
            get_safe = 'safe = source.objc_instance.safeAreaLayoutGuide().layoutFrame()' if At.safe else ''
            
            return f'''
                            {get_safe} 
                            value = ({source_value} {self.effective_gap}) {self.modifiers}
                            target_value = {target_value}
                            if {target_attribute} != target_value:
                                {target_attribute} = target_value
                            yield'''
            
        def get_opposite(self, prop):
            opposites = (
                {'left', 'right'},
                {'top', 'bottom'},
            )
            for pair in opposites:
                try:
                    pair.remove(prop)
                    return pair.pop()
                except KeyError: pass
            return None
            
        def __add__(self, other):
            self.modifiers += f'+ {other}'
            return self
            
        def __sub__(self, other):
            self.modifiers += f'- {other}'
            return self
            
        def __mul__(self, other):
            self.modifiers += f'* {other}'
            return self
            
        def __truediv__(self, other):
            self.modifiers += f'/ {other}'
            return self
            
        def __floordiv__(self, other):
            self.modifiers += f'// {other}'
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

    def _prop(attribute):
        p = property(
            lambda self:
                partial(At._getter, self, attribute)(),
            lambda self, value:
                partial(At._setter, self, attribute, value)()
        )
        return p

    def _getter(self, attr_string):
        return At.Anchor(self, attr_string)

    def _setter(self, attr_string, value):
        if value is None:
            self._remove_anchor(attr_string)
        else:
            source_anchor = value
            source_anchor.set_target(self, attr_string)
            source_anchor.start_script()
        
    def _remove_anchor(self, attr_string):        
        anchor = self.running_scripts.pop(attr_string, None)
        if anchor:
            cancel(anchor)
        
    @property
    def _heading(self):
        return self.__heading
        
    @_heading.setter
    def _heading(self, value):
        self.__heading = value
        self.view.transform = ui.Transform.rotation(
            value + self.heading_adjustment)
            
    # PUBLIC PROPERTIES
            
    left = _prop('left')
    right = _prop('right')
    top = _prop('top')
    bottom = _prop('bottom')
    center = _prop('center')
    center_x = _prop('center_x')
    center_y = _prop('center_y')
    width = _prop('width')
    height = _prop('height')
    heading = _prop('heading')
        
    
# Helper functions
    
def at(view):
    return At(view)
    
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

    
class Dock:
    
    direction_map = {
        'T': ('top', +1),
        'L': ('left', +1),
        'B': ('bottom', -1),
        'R': ('right', -1),
        'X': ('center_x', 0),
        'Y': ('center_y', 0),
        'C': ('center', 0),
    }
    
    def __init__(self, view, modifier=0):
        if not view.superview:
            raise ValueError('Cannot dock a view without a superview')
        self.view = view
        self.modifier = modifier
        
    def _dock(self, directions):
        v = at(self.view)
        sv = at(self.view.superview)
        for direction in directions:
            prop, sign = self.direction_map[direction]
            if prop != 'center':
                setattr(v, prop, getattr(sv, prop) + sign * self.modifier)
            else:
                setattr(v, prop, getattr(sv, prop))
                
    def __getattribute__(self, attr):
        '''
        Dock methods do not have to be called       
        You can just say `Dock(view).center`
        '''
        attr_object = super().__getattribute__(attr)
        if type(attr_object) == partial:
            attr_object()
            attr_object = lambda: None
        return attr_object
            
    all = partialmethod(_dock, 'TLBR')
    bottom = partialmethod(_dock, 'LBR')
    top = partialmethod(_dock, 'TLR')
    right = partialmethod(_dock, 'TBR')
    left = partialmethod(_dock, 'TLB')
    top_left = partialmethod(_dock, 'TL')
    top_right = partialmethod(_dock, 'TR')
    bottom_left = partialmethod(_dock, 'BL')
    bottom_right = partialmethod(_dock, 'BR')
    sides = partialmethod(_dock, 'LR')
    vertical = partialmethod(_dock, 'TB')
    top_center = partialmethod(_dock, 'TX')
    bottom_center = partialmethod(_dock, 'BX')
    left_center = partialmethod(_dock, 'LY')
    right_center = partialmethod(_dock, 'RY')
    center = partialmethod(_dock, 'C')
    
    def between(self, a, b):
        is_vertical = (
            abs(a.center.y - b.center.y) >
            abs(a.center.x - b.center.x)
        )
        a_a = at(a)
        a_b = at(b)
        a_self = at(self)
        if is_vertical:
            a_self.top = a_a.bottom + self.modifier
            a_self.bottom = a_b.top - self.modifier
            a_self.width = a_a.width
            a_self.center_x = a_a.center_x
        else:
            a_self.left = a_a.right + self.modifier
            a_self.right = a_b.left - self.modifier
            a_self.height = a_a.height
            a_self.center_y = a_a.center_y
        
        
def dock(view, superview=None, modifier=0) -> Dock:
    if superview:
        superview.add_subview(view)
    return Dock(view, modifier)
    
    
class Align:
    
    def __init__(self, view):
        self.anchor_view = at(view)
        
    def _align(self, prop, *others):
        for other in others:
            setattr(at(other), prop, getattr(self.anchor_view, prop))
    
    left = partialmethod(_align, 'left')
    right = partialmethod(_align, 'right')
    top = partialmethod(_align, 'top')
    bottom = partialmethod(_align, 'bottom')
    center = partialmethod(_align, 'center')
    center_x = partialmethod(_align, 'center_x')
    center_y = partialmethod(_align, 'center_y')
    width = partialmethod(_align, 'width')
    height = partialmethod(_align, 'height')
    heading = partialmethod(_align, 'heading')
    
def align(view):
    return Align(view)
    
def size_to_fit(view):
    view.size_to_fit()
    if type(view) in (ui.Button, ui.Label):
        view.frame = view.frame.inset(-At.gap, -At.gap)
    return view
        
    
if __name__ == '__main__':
    
    import ui

    
    class Marker(ui.View):
        
        def __init__(self, superview, image=None, radius=15):
            super().__init__(
                background_color='black',
                border_color='white',
                border_width=1,
            )
            self.radius = radius
            self.width = self.height = 2 * radius
            self.corner_radius = self.width/2
            superview.add_subview(self)
            
            if image:
                iv = ui.ImageView(
                    image=ui.Image(image),
                    content_mode=ui.CONTENT_SCALE_ASPECT_FIT,
                    frame=self.bounds,
                    flex='WH',
                )
                self.add_subview(iv)
    
            
    class Mover(Marker):
        
        def __init__(self, superview, **kwargs):
            super().__init__(superview,     
                image='iow:arrow_expand_24',
                **kwargs)
        
        def touch_moved(self, t):
            self.center += t.location - t.prev_location
    
    v = ui.View(
        background_color='black',
    )
    set_scripter_view(v)
    
    sv = ui.View()
    dock(sv, v, -At.gap).all()
    
    main_view = ui.Label(
        text='',
        text_color='white',
        alignment=ui.ALIGN_RIGHT,
        border_color='white',
        border_width=1,
        #background_color='red',
        frame=sv.bounds,
        flex='WH',
        touch_enabled=True,
    )
    
    menu_view = ui.Label(
        text='MENU',
        text_color='white',
        alignment=ui.ALIGN_CENTER,
        border_color='white',
        border_width=1,
        background_color='grey',
        frame=sv.bounds,
        width=300,
        flex='H'
    )
    
    sv.add_subview(menu_view)
    sv.add_subview(main_view)
    
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
    dock(menu_button, main_view).top_left()

    At(menu_view).right = At(main_view).left
    mv = At(main_view)
    
    bottom_bar = ui.View(
        background_color='grey'
    )
    main_view.add_subview(bottom_bar)
    dock(bottom_bar).bottom()

    pointer = ui.ImageView(
        image=ui.Image('iow:ios7_navigate_outline_256'),
        width=36,
        height=36,
        content_mode=ui.CONTENT_SCALE_ASPECT_FIT,
    )
    
    dock(pointer, main_view).center
    at(pointer).heading_adjustment = math.pi / 4
    
    mover = Mover(main_view)
    mover.center = (100,100)
    at(pointer).heading = at(mover).center
    
    stretcher = ui.View(
        background_color='grey',
        height=30
    )
    main_view.add_subview(stretcher)
    at(stretcher).left = at(mover).center_x
    at(stretcher).center_y = at(main_view).height * 3/4
    at(stretcher).right = at(main_view).right
    
    
    l = ui.Label(text='Demo',
        text_color='white',
        border_color='white',
        border_width=1,
        alignment=ui.ALIGN_CENTER,
    )
    size_to_fit(l)
    dock(l, main_view).top_center()
    
    
    v.present('fullscreen', 
        animated=False,
        hide_title_bar=True,
    )

