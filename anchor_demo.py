import math

import ui

from scripter import set_scripter_view

from anchor import *


def style(v):
    v.background_color = 'black'
    v.text_color = v.tint_color = v.border_color = 'white'
    v.border_width = 1
    v.alignment = ui.ALIGN_CENTER
    
    return v

def style_label(v):
    v.background_color = (0,0,0,0.5)
    v.text_color = 'white'
    v.border_color = 'transparent'
    v.border_width = 1
    v.alignment = ui.ALIGN_CENTER
    
    return v

root = ui.View(
    background_color='black',
)
set_scripter_view(root)

title_area = size_to_fit(style(ui.Label(
    text='adjust standard gap, e.g. fit tight without gap')))
dock(title_area, root, At.TIGHT).top

content_area = style(ui.View())
dock(content_area, root, At.TIGHT).bottom()

at(content_area).top = at(title_area).bottom

dock_area = style(ui.View())
#dock(dock_area, content_area).top
#at(dock_area).height = at(content_area).height / 3 - At.gaps_for(3)
flex_area = style(ui.View())
pointer_area = style(ui.View())
#dock(pointer_area, content_area).bottom
#at(pointer_area).height = at(content_area).height / 3 - At.gaps_for(3)

fill_from_top(content_area,
    dock_area,
    flex_area,
    pointer_area
)

#dock(flex_area, content_area).between(top=dock_area, bottom=pointer_area)

safe_area_note = size_to_fit(style_label(ui.Label(
    text='respect safe area by default')))
dock(safe_area_note, content_area, 1).bottom

fill_note = size_to_fit(style_label(ui.Label(
    text='stretch views to fill available area')))
content_area.add_subview(fill_note)
fill_note.transform = ui.Transform.rotation(math.pi/2)
at(fill_note).center_x = at(content_area).right - fill_note.height / 2 - At.gap - 1
at(fill_note).center_y = at(content_area).center_y
#dock(fill_note, content_area).right_center


root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

