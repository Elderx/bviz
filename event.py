from pyray import *
from raylib import *

from timer import Timer

SCREEN_W = 3840
SCREEN_H = 2160

def wrap_text(text, max_chars_per_line=40):
    words = text.split()
    lines = []
    current_line = ""
    for w in words:
        if len(current_line) + len(w) + 1 <= max_chars_per_line:
            if current_line:
                current_line += " "
            current_line += w
        else:
            lines.append(current_line)
            current_line = w
    if current_line:
        lines.append(current_line)
    return lines

class Event:
    def __init__(self, text=""):
        self.color = Color(0, 255, 0, 255)
        self.radius = 10
        self.initial_pos = Vector2(
            get_random_value(self.radius, SCREEN_W - self.radius),
            get_random_value(self.radius, SCREEN_H - self.radius)
        )
        self.pos_x = self.initial_pos.x
        self.pos_y = self.initial_pos.y
        self.current_pos = Vector2(self.pos_x, self.pos_y)
        self.direction = Vector2Normalize(
            Vector2(get_random_value(-100, 100), get_random_value(-100, 100))
        )
        self.speed = 100

        self.keep_alive_time = 5
        self.timer = Timer(self.keep_alive_time, False, True, self.on_timer_end)
        self.dead = False

        self.text = text

    def on_timer_end(self):
        self.destroy()

    def extend_life(self):
        self.timer.reset()

    def destroy(self):
        self.dead = True

    def update(self, dt, enable_movement=False):
        if enable_movement:
            self.current_pos.x += self.direction.x * self.speed * dt
            self.current_pos.y += self.direction.y * self.speed * dt

    def draw(self):
        draw_circle_v(self.current_pos, self.radius, self.color)

        # If there's text, draw it below the circle with naive wrapping
        if self.text:
            lines = wrap_text(self.text, max_chars_per_line=40)
            font_size = 20
            y_offset = self.radius + 5
            for line in lines:
                draw_text(line, int(self.current_pos.x), int(self.current_pos.y + y_offset), font_size, RAYWHITE)
                y_offset += font_size + 2
