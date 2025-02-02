from pyray import *
from raylib import *
import sys
import random
import socket
import time

from event import Event

# -------------- CONFIG ----------------
SCREEN_W, SCREEN_H = 3840, 2160
TCP_SERVER_HOST = "127.0.0.1"
TCP_SERVER_PORT = 12345
CONNECT_RETRY_INTERVAL = 2.0

enable_movement = False

events = []

sock = None
last_connect_attempt_time = 0.0

read_buffer = b""

events_in_last_second = 0
last_second_time = 0.0
displayed_events_per_second = 0
# --------------------------------------


# -------------- NETWORKING ----------------

def init_connection(host, port):
    global sock
    try:
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_sock.connect((host, port))
        tmp_sock.setblocking(False)
        sock = tmp_sock
        print(f"Connected to Python client at {host}:{port}")
    except ConnectionRefusedError:
        print(f"Could not connect to Python client! Make sure it's running on {host}:{port}.")
        sock = None

def maintain_connection(host, port):
    global sock, last_connect_attempt_time

    if sock is not None:
        return # already connected

    current_time = time.time()
    if (current_time - last_connect_attempt_time) < CONNECT_RETRY_INTERVAL:
        return

    last_connect_attempt_time = current_time
    print(f"Attempting to connect to {host}:{port}...")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
    except (ConnectionRefusedError, socket.timeout):
        print("Connection failed, will retry...")
        s.close()
        return

    s.setblocking(False)
    sock = s
    print(f"Reconnected to Python client at {host}:{port}")


def process_line(line: bytes):
    global events, events_in_last_second

    line = line.strip()
    if not line:
        return

    if line.startswith(b"NEW|"):
        text_part = line[4:].decode("utf-8", errors="ignore")

        events.append(Event(text=text_part))
        events_in_last_second += 1
        # print(f"DEBUG: Appended new event with text={text_part!r}. events size={len(events)}")

    elif line == b"NEW":
        # A bare 'NEW' with no text
        events.append(Event())
        events_in_last_second += 1
        print(f"DEBUG: Appended new event (no text). events size={len(events)}")

    else:
        print(f"DEBUG: Unrecognized line received: {line}")


def read_from_socket():
    global sock, read_buffer

    if sock is None:
        return  # not connected

    try:
        chunk = sock.recv(4096)
        if not chunk:
            # Server closed connection gracefully
            print("Connection closed by server.")
            sock.close()
            sock = None
            return

        # Append new chunk to the buffer
        read_buffer += chunk

        # Split on newlines
        lines = read_buffer.split(b"\n")

        # All but the last element in 'lines' are complete lines.
        for full_line in lines[:-1]:
            process_line(full_line)

        # The last element might be a partial line with no trailing newline
        read_buffer = lines[-1]

    except BlockingIOError:
        # No data available
        pass
    except ConnectionError:
        print("Lost connection to Python client.")
        sock.close()
        sock = None


def close_connection():
    global sock
    if sock:
        sock.close()
        sock = None



def update_events_per_second():
    global last_second_time, events_in_last_second, displayed_events_per_second
    current_time = get_time()
    if (current_time - last_second_time) >= 1.0:
        displayed_events_per_second = events_in_last_second
        events_in_last_second = 0
        last_second_time = current_time


# -------------- MAIN LOOP ----------------

def game():
    global last_second_time

    init_connection(TCP_SERVER_HOST, TCP_SERVER_PORT)

    last_second_time = get_time()

    init_window(SCREEN_W, SCREEN_H, "bViz Raylib Client")
    set_window_monitor(1)

    while not window_should_close():
        dt = get_frame_time()

        if sock is None:
            maintain_connection(TCP_SERVER_HOST, TCP_SERVER_PORT)
        else:
            read_from_socket()

        update_events_per_second()

        begin_drawing()
        clear_background(Color(0, 0, 0, 255))

        # Update & draw events
        for e in events:
            e.timer.update()
            e.update(dt, enable_movement)
            e.draw()

        # Remove dead events
        events[:] = [ev for ev in events if not ev.dead]

        # Draw FPS
        draw_fps(10, 10)

        # Show how many events per second are arriving
        draw_text(f"Events/sec: {displayed_events_per_second}", 10, 40, 20, RAYWHITE)

        end_drawing()

    close_window()
    close_connection()

game()
