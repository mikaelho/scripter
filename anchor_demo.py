import math

import ui

from scripter import set_scripter_view

from anchor import *


def style(*views):
    for v in views:
        v.background_color = 'black'
        v.text_color = v.tint_color = v.border_color = 'white'
        v.border_width = 1
        v.alignment = ui.ALIGN_CENTER
    
    return v

def style2(*views):
    for v in views:
        v.background_color = 'grey'
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
        number_of_lines=0,
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
pointer_area = create_area('heading,\ncustom,\nfunc')
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

dock(dock_area).top_center(make_label('top\ncenter'))
dock(dock_area).left(make_label('left'))
dock(dock_area).center(make_label('center'))
dock(dock_area).bottom_right(make_label('bottom\nright'))

l1 = make_label('1')
align_area.add_subview(l1)
at(l1).center_x = at(align_area).width / 4
at(l1).center_y = at(align_area).center_y
l2 = make_label('2')
align_area.add_subview(l2)
at(l2).center_x = at(align_area).width / 2
l3 = make_label('3')
align_area.add_subview(l3)
at(l3).center_x = at(align_area).width * 3 / 4
align(l1).center_y(l2, l3)
    

root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

