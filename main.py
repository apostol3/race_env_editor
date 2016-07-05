import math
import os
from enum import Enum

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.graphics import Translate, ScissorPush, ScissorPop, Scale
from kivy.graphics.vertex_instructions import Line, Quad
from kivy.lang import Builder
from kivy.properties import Property
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from map import Map

__author__ = 'leon.ljsh'


class CurrentAction(Enum):
    none = 0
    wall = 1
    headline = 2
    car = 3
    finish = 4
    edit = 5


class MapDrawer(Widget):
    action = Property(CurrentAction.none)
    grid_step = Property(6)
    max_time = Property(120)
    map_width = Property(60)
    map_height = Property(36)

    def __init__(self, **kwargs):
        super(MapDrawer, self).__init__(**kwargs)
        self.bind(pos=self.draw)
        self.bind(size=self.draw)
        self.x0_pos = 0
        self.y0_pos = 0
        self.x1_pos = 0
        self.y1_pos = 0
        self.camx = 0
        self.camy = 0
        self.zoom = 1 / 10
        self.selection_r = 7.5
        self.faulted_click = True
        self.colors = {'bg': (0, 0, 0), 'grid': (0.2, 0.2, 0.2), 'wall': (0.68, 1, 0.6), 'main_line': (0.05, 0.2, 0.28),
                       'selected_car': (0.86, 0.78, 0.65), 'finish': (0.6, 0.65, 0.8), 'selection': (0.9, 0.9, 0.9)}
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_up)
        self.sel = None

    def fs(self, x, y):
        return x * self.zoom - self.camx, y * self.zoom - self.camy

    def set_action(self, action):
        if action == CurrentAction.wall:
            app.map.start_new_wall()
        elif action == CurrentAction.headline:
            app.map.headline.clear()
        elif action == CurrentAction.car:
            pass
        elif action == CurrentAction.edit:
            self.sel = None
            self.move_sel = False
        elif action == CurrentAction.none:
            pass

        self.action = action
        self.draw()

    def select_wall(self, x, y):
        sel_r = self.selection_r * self.zoom
        for i in range(len(app.map.walls)):
            wall = app.map.walls[i]
            for j in range(len(wall)):
                point = wall[j]
                if (point[0] - x) ** 2 + (point[1] - y) ** 2 < sel_r ** 2:
                    return 'wall', i, j

    def select_headline(self, x, y):
        sel_r = self.selection_r * self.zoom
        for i in range(len(app.map.headline)):
            point = app.map.headline[i]
            if (point[0] - x) ** 2 + (point[1] - y) ** 2 < sel_r ** 2:
                return 'headline', i

    def select_finish(self, x, y):
        sel_r = self.selection_r * self.zoom
        for i in range(len(app.map.finish)):
            point = app.map.finish[i]
            if (point[0] - x) ** 2 + (point[1] - y) ** 2 < sel_r ** 2:
                return 'finish', i

    def select_car(self, x, y):
        sel_r2 = app.map.car_size[0] ** 2 + app.map.car_size[1] ** 2
        for i in range(len(app.map.cars)):
            car = app.map.cars[i]
            if (car[0] - x) ** 2 + (car[1] - y) ** 2 < sel_r2:
                return 'car', i

    def select_something(self, x, y):
        car = self.select_car(x, y)
        if car:
            return car
        headline = self.select_headline(x, y)
        if headline:
            return headline
        wall = self.select_wall(x, y)
        if wall:
            return wall
        finish = self.select_finish(x, y)
        if finish:
            return finish

    def on_button_left_down(self, touch):
        self.x0_pos, self.y0_pos = touch.pos[0] - self.pos[0], -touch.pos[1] - self.pos[1] + self.size[1]
        if self.action == CurrentAction.edit:
            x, y = self.fs(self.x0_pos, self.y0_pos)
            self.sel = self.select_something(x, y)

        self.draw()

    def on_button_left_move(self, touch):
        self.x1_pos, self.y1_pos = touch.pos[0] - self.pos[0], -touch.pos[1] - self.pos[1] + self.size[1]
        if self.action == CurrentAction.none or (self.action == CurrentAction.edit and self.sel is None):
            self.camx += (self.x1_pos - self.x0_pos) * self.zoom
            self.camy += (self.y1_pos - self.y0_pos) * self.zoom
            self.camx = max(min(self.camx, self.width * self.zoom), -app.map.size[0])
            self.camy = max(min(self.camy, self.height * self.zoom), -app.map.size[1])
        elif self.action == CurrentAction.edit and self.sel is not None:
            x, y = self.fs(self.x1_pos, self.y1_pos)
            if self.sel[0] == 'wall':
                app.map.walls[self.sel[1]][self.sel[2]] = (x, y)
            elif self.sel[0] == 'headline':
                app.map.headline[self.sel[1]] = (x, y)
            elif self.sel[0] == 'finish':
                app.map.finish[self.sel[1]] = (x, y)
            elif self.sel[0] == 'car':
                app.map.cars[self.sel[1]] = (x, y, app.map.cars[self.sel[1]][2])

        self.x0_pos = self.x1_pos
        self.y0_pos = self.y1_pos

        self.draw()

    def on_button_left_up(self, touch):
        self.x1_pos, self.y1_pos = touch.pos[0] - self.pos[0], -touch.pos[1] - self.pos[1] + self.size[1]
        x, y = self.fs(self.x1_pos, self.y1_pos)
        if self.action == CurrentAction.none:
            pass
        elif self.action == CurrentAction.wall:
            app.map.append_wall_point(x, y)
        elif self.action == CurrentAction.headline:
            app.map.append_headline_point(x, y)
        elif self.action == CurrentAction.car:
            app.map.create_car(x, y)
        elif self.action == CurrentAction.finish:
            app.map.append_finish_point(x, y)
        self.draw()

    def on_button_right_up(self, touch):
        pass

    def on_button_right_down(self, touch):
        pass

    def on_scrolldown(self, touch):
        if self.zoom < 0.01:
            return
        self.zoom /= 1.05
        self.camx -= self.zoom * 0.05 * (touch.pos[0] - self.pos[0])
        self.camy -= self.zoom * 0.05 * (-touch.pos[1] - self.pos[1] + self.size[1])
        self.draw()

    def on_scrollup(self, touch):
        if self.zoom > 1:
            return
        self.zoom *= 1.05
        self.camx += self.zoom * (0.05 / 1.05) * (touch.pos[0] - self.pos[0])
        self.camy += self.zoom * (0.05 / 1.05) * (-touch.pos[1] - self.pos[1] + self.size[1])
        self.draw()

    def on_touch_down(self, touch):
        if not (self.pos[0] < touch.pos[0] < self.pos[0] + self.size[0] and
                            self.pos[1] < touch.pos[1] < self.pos[1] + self.size[1]):
            return
        self.faulted_click = False
        if touch.button == 'left':
            self.on_button_left_down(touch)
        elif touch.button == 'right':
            self.on_button_right_down(touch)
        elif touch.button == 'scrolldown':
            self.on_scrolldown(touch)
        elif touch.button == 'scrollup':
            self.on_scrollup(touch)

    def on_touch_up(self, touch):
        if self.faulted_click:
            return
        if touch.button == 'left':
            self.on_button_left_up(touch)
        elif touch.button == 'right':
            self.on_button_right_up(touch)

        self.faulted_click = True

    def on_touch_move(self, touch):
        if self.faulted_click:
            return
        if touch.button == 'left':
            self.on_button_left_move(touch)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_up=self._on_keyboard_up)
        self._keyboard = None

    def _on_keyboard_up(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'w':
            app.map.start_new_wall()
            self.set_action(CurrentAction.wall)
        elif keycode[1] == 'h':
            self.set_action(CurrentAction.headline)
        elif keycode[1] == 'c':
            self.set_action(CurrentAction.car)
        elif keycode[1] == 'f':
            self.set_action(CurrentAction.finish)
        elif keycode[1] == 'e':
            self.set_action(CurrentAction.edit)
        elif keycode[1] == 'escape':
            self.set_action(CurrentAction.none)
        elif keycode[1] == 'numpadadd' and len(app.map.cars) > 0:
            app.map.cars[-1] = (app.map.cars[-1][0], app.map.cars[-1][1], app.map.cars[-1][2] + 0.1)
        elif keycode[1] == 'numpadsubstract' and len(app.map.cars) > 0:
            app.map.cars[-1] = (app.map.cars[-1][0], app.map.cars[-1][1], app.map.cars[-1][2] - 0.1)
        self.draw()
        return True

    def draw(self, *_):
        self.canvas.clear()

        with self.canvas:
            ScissorPush(x=self.pos[0], y=self.pos[1], width=self.size[0], height=self.size[1])
            Color(*self.colors['bg'])
            Translate(self.pos[0], self.pos[1] + self.size[1])
            Scale(1 / self.zoom, -1 / self.zoom, 1)
            Rectangle(pos=(0, 0), size=self.size)
            Translate(self.camx, self.camy)
            self.inner_draw()
            Translate(-self.camx, -self.camy)
            Scale(self.zoom, self.zoom, 1)
            Color(0, 0, 0)
            Scale(1, -1, 1)
            Translate(-self.pos[0], -self.pos[1] - self.size[1])

            ScissorPop()

    def inner_draw(self):
        sel_r = self.selection_r * self.zoom
        show_selection_areas = self.action == CurrentAction.edit

        Color(*self.colors['grid'])
        for i in range(0, app.map.size[0], self.grid_step):
            Line(points=(i, 0, i, app.map.size[1]))
        for i in range(0, app.map.size[1], self.grid_step):
            Line(points=(0, i, app.map.size[0], i))

        Color(*self.colors['finish'], 0.8)
        if len(app.map.finish) == 2:
            Rectangle(pos=app.map.finish[0],
                      size=(app.map.finish[1][0] - app.map.finish[0][0], app.map.finish[1][1] - app.map.finish[0][1]))

        if show_selection_areas:
            Color(*self.colors['finish'], 0.3)
            for point in app.map.finish:
                Ellipse(pos=(point[0] - sel_r, point[1] - sel_r),
                        size=(sel_r * 2, sel_r * 2))

        Color(*self.colors['wall'])
        Line(rectangle=(0, 0, app.map.size[0], app.map.size[1]))
        for wall in app.map.walls:
            for i in range(len(wall) - 1):
                Line(points=(wall[i][0], wall[i][1], wall[i + 1][0], wall[i + 1][1]))

        if show_selection_areas:
            Color(*self.colors['wall'], 0.3)
            for wall in app.map.walls:
                for point in wall:
                    Ellipse(pos=(point[0] - sel_r, point[1] - sel_r),
                            size=(sel_r * 2, sel_r * 2))

        Color(*self.colors['main_line'])
        for i in range(len(app.map.headline) - 1):
            Line(points=(
                app.map.headline[i][0], app.map.headline[i][1], app.map.headline[i + 1][0],
                app.map.headline[i + 1][1]))

        if show_selection_areas:
            Color(*self.colors['main_line'], 0.3)
            for point in app.map.headline:
                Ellipse(pos=(point[0] - sel_r, point[1] - sel_r),
                        size=(sel_r * 2, sel_r * 2))

        Color(*self.colors['selected_car'])
        sz = app.map.car_size
        for x, y, a in app.map.cars:
            Quad(points=(
                x + sz[0] * math.cos(a) - sz[1] * math.sin(a), y - sz[0] * math.sin(a) - sz[1] * math.cos(a),
                x - sz[0] * math.cos(a) - sz[1] * math.sin(a), y + sz[0] * math.sin(a) - sz[1] * math.cos(a),
                x - sz[0] * math.cos(a) + sz[1] * math.sin(a), y + sz[0] * math.sin(a) + sz[1] * math.cos(a),
                x + sz[0] * math.cos(a) + sz[1] * math.sin(a), y - sz[0] * math.sin(a) + sz[1] * math.cos(a))
            )

        Color(*self.colors['bg'], 0.5)
        for x, y, a in app.map.cars:
            Ellipse(pos=(x - sz[1] * math.sin(a) / 2 - 0.15, y - sz[1] * math.cos(a) / 2 - 0.15), size=(0.3, 0.3))

        if self.action == CurrentAction.edit and self.sel is not None:
            def draw_selected_point(point, color):
                Color(*color, 0.5)
                Ellipse(pos=(point[0] - sel_r, point[1] - sel_r),
                        size=(sel_r * 2, sel_r * 2))
                Color(*self.colors['selection'], 1)
                Line(ellipse=(point[0] - sel_r, point[1] - sel_r, sel_r * 2, sel_r * 2))

            if self.sel[0] == 'wall':
                draw_selected_point(app.map.walls[self.sel[1]][self.sel[2]], self.colors['wall'])
            if self.sel[0] == 'headline':
                draw_selected_point(app.map.headline[self.sel[1]], self.colors['main_line'])
            if self.sel[0] == 'finish':
                draw_selected_point(app.map.finish[self.sel[1]], self.colors['finish'])
            if self.sel[0] == 'car':
                x, y, a = app.map.cars[self.sel[1]]
                Color(*self.colors['selection'], 1)
                Line(points=(
                    x + sz[0] * math.cos(a) - sz[1] * math.sin(a), y - sz[0] * math.sin(a) - sz[1] * math.cos(a),
                    x - sz[0] * math.cos(a) - sz[1] * math.sin(a), y + sz[0] * math.sin(a) - sz[1] * math.cos(a),
                    x - sz[0] * math.cos(a) + sz[1] * math.sin(a), y + sz[0] * math.sin(a) + sz[1] * math.cos(a),
                    x + sz[0] * math.cos(a) + sz[1] * math.sin(a), y - sz[0] * math.sin(a) + sz[1] * math.cos(a)),
                    width=1.3 * self.zoom, close=True
                )


class MainWindow(App):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.map = Map(60, 36)
        self.drawer = None

    def build(self):
        self.root = Builder.load_file('main_window.kv')
        self.drawer = self.root.ids.drawer

    def on_wall_press(self, state):
        if state == 'down':
            self.drawer.set_action(CurrentAction.wall)
        else:
            self.drawer.set_action(CurrentAction.none)

    def on_headline_press(self, state):
        if state == 'down':
            self.drawer.set_action(CurrentAction.headline)
        else:
            self.drawer.set_action(CurrentAction.none)

    def on_car_press(self, state):
        if state == 'down':
            self.drawer.set_action(CurrentAction.car)
        else:
            self.drawer.set_action(CurrentAction.none)

    def on_finish_press(self, state):
        if state == 'down':
            self.drawer.set_action(CurrentAction.finish)
        else:
            self.drawer.set_action(CurrentAction.none)

    def on_edit_press(self, state):
        if state == 'down':
            self.drawer.set_action(CurrentAction.edit)
        else:
            self.drawer.set_action(CurrentAction.none)

    def on_new(self):

        self.map = Map(self.drawer.map_width, self.drawer.map_height)
        self.drawer.set_action(CurrentAction.none)

    def on_step_validate(self, text, text_input):
        try:
            self.drawer.grid_step = int(text)
        except ValueError:
            text_input.text = str(self.drawer.grid_step)

    def on_time_validate(self, text, text_input):
        try:
            self.drawer.max_time = int(text)
        except ValueError:
            text_input.text = str(self.drawer.max_time)

    def on_map_width_validate(self, text, text_input):
        try:
            self.drawer.map_width = int(text)
        except ValueError:
            text_input.text = str(self.drawer.map_width)

    def on_map_height_validate(self, text, text_input):
        try:
            self.drawer.map_height = int(text)
        except ValueError:
            text_input.text = str(self.drawer.map_height)

    def open_file_dialog(self, *_):
        OpenMapPopup(self.open_file).open()

    def save_file_dialog(self, *_):
        SaveMapPopup(self.save_file).open()

    def open_file(self, file):
        self.map = Map.open_from_file(file)
        self.drawer.map_width, self.drawer.map_height = self.map.size
        self.drawer.max_time = self.map.max_time
        self.drawer.draw()

    def save_file(self, file):
        self.map.max_time = self.drawer.max_time
        self.map.save_to_file(file)


class OpenMapPopup(Popup):
    def __init__(self, then, **kwargs):
        super(OpenMapPopup, self).__init__(**kwargs)
        self.then = then

    def selection_cb(self, *_):
        if len(self.ids.file_chooser.selection) != 0:
            self.ids.file_input.text = os.path.basename(self.ids.file_chooser.selection[0])

    def choose_cb(self, *_):
        self.ids.file_input.text = os.path.basename(self.ids.file_chooser.selection[0])
        self.ok_cb()

    def path_cb(self, *_):
        self.ids.cur_path.text = os.path.abspath(self.ids.file_chooser.path) + os.path.sep

    def cancel_cb(self):
        self.dismiss()

    def ok_cb(self, *_):
        self.dismiss()
        self.then(os.path.join(self.ids.file_chooser.path, self.ids.file_input.text))


class SaveMapPopup(OpenMapPopup):
    def __init__(self, *args, **kwargs):
        super(SaveMapPopup, self).__init__(*args, **kwargs)
        self.title = 'Save map'

    def ok_cb(self, *_):
        fname = self.ids.file_input.text + ('.json' if self.ids.file_input.text.find('.') == -1 else '')
        if os.path.exists(fname):
            ask = OkCancelPopup('Warning', 'File "{}" already exists\nOverwrite it?'.format(fname), self.ask_ok,
                                self.ask_no)
            ask.open()
        else:
            self.ask_ok()

    def ask_ok(self, *_):
        self.dismiss()
        fname = self.ids.file_input.text + ('.json' if self.ids.file_input.text.find('.') == -1 else '')
        self.then(os.path.join(self.ids.file_chooser.path, fname))

    def ask_no(self, *_):
        pass


class OkCancelPopup(Popup):
    def __init__(self, title, text, ok_cb, cancel_cb, **kwargs):
        super(OkCancelPopup, self).__init__(**kwargs)
        self.ok_cb = ok_cb
        self.cancel_cb = cancel_cb
        self.title = title
        self.ids.message_label.text = text


app = MainWindow(title="Map editor for race_env")
app.run()
