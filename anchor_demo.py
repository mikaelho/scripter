import math

import ui

from scripter import set_scripter_view

from anchor import *


def style(*views):
    for v in views:
        view = v
        v.background_color = 'black'
        v.text_color = v.tint_color = v.border_color = 'white'
        v.border_width = 1
        v.alignment = ui.ALIGN_CENTER
    
    return v

def style_label(v):
    v.background_color = (0,0,0,0.5)
    v.text_color = 'white'
    v.alignment = ui.ALIGN_CENTER
    
    return v

root = ui.View(
    background_color='black',
)
set_scripter_view(root)

button_area = style(ui.View())
dock(root).bottom(button_area, At.TIGHT)
buttons = [
    size_to_fit(style(ui.Button(
        title=f'button {i + 1}')))
    for i in range(6)
]
flow(button_area).from_top_left(*buttons)
at(button_area).height = at(button_area).fit_height

content_area = style(ui.View())
dock(root).top(content_area, At.TIGHT)
at(content_area).bottom = at(button_area).top - At.TIGHT

at_area = style(ui.Label(text='basic at & flex'))
pointer_area = style(ui.Label(text='pointer'))
dock_area = style(ui.View())
align_area = style(ui.Label(text='align'))

fill(content_area, 2).from_top(
    at_area,
    dock_area,
    pointer_area,
    align_area,
)

def make_label(text):
    return size_to_fit(style(ui.Label(
        text=text,
        number_of_lines=0)))

dock(dock_area).top_center(make_label('top\ncenter'))
dock(dock_area).left(make_label('left'))
dock(dock_area).center(make_label('center'))
dock(dock_area).bottom_right(make_label('bottom\nright'))

root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

