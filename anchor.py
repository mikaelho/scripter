
import json
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
        regular: source.center[0]
        container: source.bounds.center()[0]
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
        attribute: width
        same: value
    source:
        regular: width
        container: width - 2 * gap
"""

template = """
attr:
    type: 
    target:
        attribute: 
        leading: 
        trailing: 
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
                    while True:
                        value = {source_value}
                        gap = {At.gap}
                        target_value = {target_value}
                        if {target_attribute} != target_value:
                            {target_attribute} = target_value
                        yield
                        
                self.target_at.running_scripts[self.target_prop] = \
                    anchor_runner(self.source_at.view, self.target_at.view)
                '''
            )
            
            exec(textwrap.dedent(script_str))
    
    def __new__(cls, view):
        try:
            return view._scripter_at
        except AttributeError:
            at = super().__new__(cls)
            at.view = view
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

    def _setter(self, attr_string, *value):
        source_anchor = value[0]
        source_anchor.set_target(self, attr_string)
        source_anchor.start_script()
            
    left = _prop('left')
    right = _prop('right')
    top = _prop('top')
    bottom = _prop('bottom')
    center = _prop('center')
    center_x = _prop('center_x')
    

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
        
        def __init__(self, superview):
            super().__init__(
                width=30,
                height=30,
                corner_radius=15,
                background_color='grey'
            )
            superview.add_subview(self)
            
    
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
        text='MAIN',
        text_color='white',
        alignment=ui.ALIGN_CENTER,
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
    At(m1).top = At(main_view).top
    At(m1).center_x = At(main_view).center_x
    
    m2 = Marker(main_view)
    At(m2).center = At(main_view).center
    
    v.present('fullscreen', 
        animated=False
    )

