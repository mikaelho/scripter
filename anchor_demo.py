import ui

from scripter import set_scripter_view

from anchor import *


def style(v):
    v.background_color = 'black'
    v.text_color = v.tint_color = v.border_color = 'white'
    v.border_width = 1
    v.alignment = ui.ALIGN_CENTER
    
    return v


root = ui.View(
    background_color='black',
)
set_scripter_view(root)

safe_area = style(ui.View())
dock(safe_area, root, At.TIGHT).all()

title_area = size_to_fit(style(ui.Label(text='title')))
dock(title_area, safe_area, At.TIGHT).top



root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

