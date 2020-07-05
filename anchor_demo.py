import math

import ui

from scripter import set_scripter_view

from scripter.anchor import *


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

# ------ Button flow

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

vertical_bar = style(ui.View(width=10))
at_area.add_subview(vertical_bar)
at(vertical_bar).center_x = at(at_area).width / 5
align(at_area).center_y(vertical_bar)
at(vertical_bar).height = at(at_area).height * 0.75

fix_left = make_label('fix left')
at_area.add_subview(fix_left)
at(fix_left).left = at(vertical_bar).right
align(vertical_bar, -30).center_y(fix_left)

flex = make_label('fix left and right')
at_area.add_subview(flex)
at(flex).left = at(vertical_bar).right + At.TIGHT
at(flex).right = at(at_area).right
align(vertical_bar, +30).center_y(flex)

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

pointer = make_symbol('↣')
pointer.text_color = accent_color
pointer.background_color = 'transparent'
pointer.font = (pointer.font[0], 40)
align(pointer_area).center(pointer)
at(pointer).heading = at(target).center

heading_label = ui.Label(text='000°',
    font=('Arial Rounded MT Bold', 12),
    text_color=accent_color,
    alignment=ui.ALIGN_CENTER,
)
heading_label.size_to_fit()
pointer_area.add_subview(heading_label)
at(heading_label).center_y = at(pointer).center_y - 22
align(pointer).center_x(heading_label)

attr(heading_label).text = at(pointer).heading + (
    lambda angle: f"{int(math.degrees(angle))%360:03}°"
)

#  ----- Dock

dock(dock_area).top_center(make_label('top\ncenter'))
dock(dock_area).left(make_label('left'))
dock(dock_area).bottom_right(make_label('bottom\nright'))
center_label = make_label('center')
dock(dock_area).center(center_label)
#dock(center_label).above(make_label('below'))

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
    

# ------ Markers

show_markers = False

if show_markers:

    marker_counter = 0
    
    def create_marker(superview):
        global marker_counter
        marker_counter += 1
        marker = make_label(str(marker_counter))
        superview.add_subview(marker)
        marker.background_color = 'white'
        marker.border_color = 'black'
        marker.border_width = 1
        size_to_fit(marker)
        marker.width = marker.height
        marker.objc_instance.clipsToBounds = True
        marker.corner_radius = marker.width / 2
        return marker
        
    m1 = create_marker(at_area)
    align(fix_left).center_y(m1)
    at(m1).left = at(fix_left).right
    
    m2 = create_marker(at_area)
    align(flex).left(m2)
    at(m2).center_y = at(flex).top - At.gap
    
    m3 = create_marker(at_area)
    align(flex).right(m3)
    at(m3).center_y = at(flex).top - At.gap
    
    m4 = create_marker(pointer_area)
    at(m4).top = at(pointer).bottom + 3*At.TIGHT
    at(m4).left = at(pointer).right + 3*At.TIGHT
    
    m5 = create_marker(pointer_area)
    align(heading_label).center_y(m5)
    at(m5).left = at(heading_label).right
    
    m6 = create_marker(dock_area)
    at(m6).center_x = at(dock_area).center_x * 1.5
    at(m6).center_y = at(dock_area).center_y / 2
    
    m7 = create_marker(align_area)
    align(align_area).center_x(m7)
    at(m7).top = at(l2).bottom
    
    mc = create_marker(content_area)
    at(mc).center = at(content_area).center
    
    mb = create_marker(button_area)
    last_button = buttons[-1]
    align(last_button).center_y(mb)
    at(mb).left = at(last_button).right
    
    mr = create_marker(root)
    align(button_area).center_x(mr)
    at(mr).center_y = at(button_area).top
    
    ms = create_marker(root)
    at(ms).center_x = at(button_area).center_x * 1.5
    at(ms).center_y = at(button_area).bottom

root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

