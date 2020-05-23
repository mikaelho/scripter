from scripter import script, cancel, width


def prop(func):
    return property(func, func)

class At:
    
    gap = 8  # Apple Standard gap
    
    def __new__(cls, view):
        try:
            return view._scripter_at
        except AttributeError:
            at = super().__new__(cls)
            at.view = view
            view._scripter_at = at
            return at

    @prop
    def right(self, *value):
        try:
            def target(*values, trailing=False):
                try:
                    self.view.x = values[0] - self.view.width - (
                        0 if trailing else 8
                    )
                except:
                    return self.view.frame.max_x + (
                        0 if trailing else self.gap
                    )
            try:
                cancel(self._right_gen)
            except: pass
            self._right_gen = value[0](target)
        except Exception as error:
            print(error)
            @script
            def update(target):
                while True:
                    if self.view.frame.max_x != target(trailing=True):
                        target(self.view.frame.max_x, trailing=True)
                    yield 
            return update
            
    @prop
    def left(self, *value):
        try:
            def target(*values, trailing=False):
                try:
                    self.view.x = values[0] + (
                        self.gap if trailing else 0
                    )
                except:
                    return self.view.x - (
                        self.gap if trailing else 0
                    )
            try:
                cancel(self._left_gen)
            except: pass
            self._left_gen = value[0](target)
        except Exception as error:
            print(error)
            @script
            def update(target):
                while True:
                    if self.view.x != target():
                        target(self.view.x)
                    yield
            return update

    
    
if __name__ == '__main__':
    
    import ui
    
    v = ui.View()
    
    left_view = ui.View(
        border_color='white',
        border_width=1,
        background_color='blue',
        frame=v.bounds,
        flex='WHRB'
    )
    left_view.width = 10
    left_view.height = 10
    
    right_view = ui.View(
        border_color='white',
        border_width=1,
        background_color='red',
        frame=v.bounds,
        flex='WH'
    )
    right_view.width = v.bounds.width/3
    
    v.add_subview(left_view)
    v.add_subview(right_view)
    
    v.present('fullscreen')
    
    left_view.bring_to_front()
    
    At(right_view).left = At(left_view).right
    
    width(left_view, 300)
