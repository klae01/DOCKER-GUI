#!/usr/bin/env python3
import json
import os
import socket
import threading

from Xlib import XK, X, display
from Xlib.ext import xtest

# Global key state dictionary
key_states = {}

# Open display (Xvfb is running on :99)
d = display.Display(os.environ.get("DISPLAY", ":99"))

def handle_key(cmd):
    """Handle key press/release commands."""
    action = cmd.get("action")
    key_str = cmd.get("key")
    # Convert key string to keysym
    keysym = XK.string_to_keysym(key_str)
    if keysym == 0:
        print("Invalid keysym for:", key_str)
        return
    keycode = d.keysym_to_keycode(keysym)
    if action == "press":
        xtest.fake_input(d, X.KeyPress, keycode)
        key_states[keycode] = 1
    elif action == "release":
        xtest.fake_input(d, X.KeyRelease, keycode)
        key_states[keycode] = 0
    else:
        print("Unknown key action:", action)
    d.flush()

def handle_mouse(cmd):
    """Handle mouse move, click, and scroll commands."""
    action = cmd.get("action")
    if action == "move":
        dx = int(cmd.get("dx", 0))
        dy = int(cmd.get("dy", 0))
        pointer = d.screen().root.query_pointer()
        new_x = pointer.root_x + dx
        new_y = pointer.root_y + dy
        xtest.fake_input(d, X.MotionNotify, x=new_x, y=new_y)
        d.flush()
    elif action == "click":
        button = cmd.get("button", "left").lower()
        state = cmd.get("state")
        # Map button names to button numbers
        button_num = ["left", "middle", "right"].index(button) + 1
        if state == "press":
            xtest.fake_input(d, X.ButtonPress, button_num)
        elif state == "release":
            xtest.fake_input(d, X.ButtonRelease, button_num)
        else:
            print("Unknown mouse click state:", state)
        d.flush()
    elif action == "scroll":
        direction = cmd.get("direction", "up").lower()
        amount = int(cmd.get("amount", 1))
        button_num = ["up", "down", "left", "right"].index(direction) + 4
        for _ in range(amount):
            xtest.fake_input(d, X.ButtonPress, button_num)
            xtest.fake_input(d, X.ButtonRelease, button_num)
        d.flush()
    else:
        print("Unknown mouse action:", action)

def handle_query(cmd, conn):
    """Handle query commands."""
    resp = json.dumps({"state": key_states}) + "\n"
    conn.sendall(resp.encode("utf-8"))

op_handlers = {
    "key": lambda cmd, conn: handle_key(cmd),
    "mouse": lambda cmd, conn: handle_mouse(cmd),
    "query": handle_query,
}

def handle_client(conn):
    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    cmd = json.loads(line)
                    op = cmd.get("op")
                    if op in op_handlers:
                        op_handlers[op](cmd, conn)
                    else:
                        print("Unknown op:", op)
                except Exception as ex:
                    print("Command processing error:", ex)
    except Exception as ex:
        print("Connection error:", ex)
    finally:
        conn.close()


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 7200))
    s.listen(5)
    print("Raw input server running on port 7200")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
