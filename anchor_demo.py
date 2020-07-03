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

title_area = size_to_fit(ui.Label(
    text='adjust standard gap, e.g. fit tight without gap'))
dock(title_area, root, At.TIGHT).top

content_area = ui.View()
dock(content_area, root, At.TIGHT).bottom()
at(content_area).top = at(title_area).bottom + At.TIGHT

button_area = ui.View()
flex_area = ui.View()
pointer_area = ui.View()

'''
fill(content_area).from_top(
    button_area,
    flex_area,
    pointer_area
)
'''

buttons = [
    size_to_fit(ui.Button(
        title=f'button {i + 1}'))
    for i in range(10)
]
for btn in buttons:
    button_area.add_subview(btn)
flow(button_area).from_top_left(*buttons)

dock(button_area, content_area).top
at(button_area).height = at(button_area).fit_height

style(
    title_area,
    content_area,
    button_area,
    #flex_area,
    #pointer_area,
    *buttons,
)

safe_area_note = size_to_fit(style_label(ui.Label(
    text='respect safe area by default')))
dock(safe_area_note, content_area, 1).bottom

# Rotation makes things complicated
fill_note = size_to_fit(style_label(ui.Label(
    text='stretch views to fill available area')))
content_area.add_subview(fill_note)
fill_note.transform = ui.Transform.rotation(math.pi/2)
at(fill_note).center_x = at(content_area).right - fill_note.height / 2 - At.gap - 1
at(fill_note).center_y = at(content_area).center_y

root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

