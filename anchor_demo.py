import math

import ui

from scripter import set_scripter_view

from anchor import *


accent_color = '#cae8ff'

def style(*views):
    for v in views:
        v.background_color = 'black'
        v.text_color = v.tint_color = v.border_color = 'white'
        v.border_width = 1
        v.alignment = ui.ALIGN_CENTER
    
    return v

def style2(*views):
    for v in views:
        v.background_color = accent_color
        v.text_color = v.tint_color = 'black'
        v.alignment = ui.ALIGN_CENTER
        v.font = ('Arial Rounded MT Bold', 12)
    
    return v

def style_label(v):
    v.background_color = 'black'
    v.text_color = 'white'
    v.alignment = ui.ALIGN_CENTER
    return v
    
def create_area(title):
    area = style(ui.View())
    label = style_label(size_to_fit(ui.Label(
        text=title.upper(),
        #number_of_lines=0,
        font=('Arial Rounded MT Bold', 12),
    )))
    dock(area).top_right(label, At.TIGHT)
    return area

root = ui.View(
    background_color='black',
)
set_scripter_view(root)

button_area = style(ui.View())
dock(root).bottom(button_area, At.TIGHT)
button_label = style_label(ui.Label(
    text='FLOW',
    font=('Arial Rounded MT Bold', 12),
))
button_label.size_to_fit()
ghost_area = ui.View()
root.add_subview(ghost_area)
at(ghost_area).frame = at(button_area).frame
dock(ghost_area).bottom_right(button_label)
buttons = [
    size_to_fit(style2(ui.Button(
        title=f'button {i + 1}')))
    for i in range(6)
]
flow(button_area).from_top_left(*buttons)
at(button_area).height = at(button_area).fit_height

content_area = style(ui.View())
dock(root).top(content_area, At.TIGHT)
at(content_area).bottom = at(button_area).top - At.TIGHT

at_area = create_area('basic at & flex')
pointer_area = create_area('heading, custom, func')
dock_area = create_area('dock')
align_area = create_area('align')

fill(content_area, 2).from_top(
    at_area,
    dock_area,
    pointer_area,
    align_area,
)

def make_label(text):
    return size_to_fit(style2(ui.Label(
        text=text,
        number_of_lines=0)))

#  ----- At & flex

bulwark = style(ui.View(width=10))
at_area.add_subview(bulwark)
at(bulwark).center_x = at(at_area).width / 5
align(at_area).center_y(bulwark)
at(bulwark).height = at(at_area).height * 0.75

basic_at = make_label('fix left')
at_area.add_subview(basic_at)
at(basic_at).left = at(bulwark).right
align(bulwark, -30).center_y(basic_at)

flex = make_label('fix left and right')
at_area.add_subview(flex)
at(flex).left = at(bulwark).right + At.TIGHT
at(flex).right = at(at_area).right
align(bulwark, +30).center_y(flex)

# ------ Heading & custom

def make_symbol(character):
    symbol = make_label(character)
    symbol.font = ('Arial Rounded MT Bold', 18)
    pointer_area.add_subview(symbol)
    size_to_fit(symbol)
    symbol.width = symbol.height
    symbol.objc_instance.clipsToBounds = True
    symbol.corner_radius = symbol.width / 2
    return symbol

target = make_symbol('⌾')
target.font = (target.font[0], 44)
at(target).center_x = at(pointer_area).center_x / 1.75
at(target).center_y = at(pointer_area).height - 60

pointer = make_symbol('→')
pointer.font = (pointer.font[0], 28)
align(pointer_area).center(pointer)
at(pointer).heading = at(target).center

heading_label = ui.Label(text='000',
    font=('Anonymous Pro', 12),
    text_color=accent_color,
    alignment=ui.ALIGN_CENTER,
)
heading_label.size_to_fit()
pointer_area.add_subview(heading_label)
at(heading_label).center_x = at(pointer).center_x
at(heading_label).top = at(pointer).center_y + 25

attr(heading_label).text = at(pointer).heading + (
    lambda angle: f"{int(math.degrees(angle))%360:03}"
)

#  ----- Dock

dock(dock_area).top_center(make_label('top\ncenter'))
dock(dock_area).left(make_label('left'))
dock(dock_area).center(make_label('center'))
dock(dock_area).bottom_right(make_label('bottom\nright'))

#  ----- Align

l1 = make_label('1')
align_area.add_subview(l1)
at(l1).center_x = at(align_area).center_x / 2
l2 = make_label('2')
align_area.add_subview(l2)
at(l2).center_x = at(align_area).center_x
l3 = make_label('3')
align_area.add_subview(l3)
at(l3).center_x = at(align_area).center_x / 2 * 3

align(align_area).center_y(l1, l2, l3)
    

root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

