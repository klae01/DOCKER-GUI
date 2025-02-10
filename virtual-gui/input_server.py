#!/usr/bin/env python3
import json
import os
import socket

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
        abs_mode = "x" in cmd or "y" in cmd
        rel_mode = "dx" in cmd or "dy" in cmd
        pointer = d.screen().root.query_pointer()

        if abs_mode and not rel_mode:
            x = int(v if (v := cmd.get("x")) is not None else pointer.root_x)
            y = int(v if (v := cmd.get("y")) is not None else pointer.root_y)
        elif not abs_mode and rel_mode:
            x = pointer.root_x + int(v if (v := cmd.get("dx")) is not None else 0)
            y = pointer.root_y + int(v if (v := cmd.get("dy")) is not None else 0)
        else:
            print(
                f"Error: Provide either absolute (x={cmd.get('x')}, y={cmd.get('y')}) or "
                f"relative (dx={cmd.get('dx')}, dy={cmd.get('dy')}) parameters exclusively."
            )
            return
        xtest.fake_input(d, X.MotionNotify, x=x, y=y)
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
            d.flush()
            xtest.fake_input(d, X.ButtonRelease, button_num)
            d.flush()
    else:
        print("Unknown mouse action:", action)


def handle_query(cmd, conn):
    """Handle query commands for keyboard and/or mouse"""
    target_str = cmd.get("target", "keyboard|mouse")
    targets = target_str.strip().lower().split("|")

    result = {}
    if "keyboard" in targets:
        result["keyboard"] = key_states
    if "mouse" in targets:
        pointer = d.screen().root.query_pointer()
        result["mouse"] = {
            "x": pointer.root_x,
            "y": pointer.root_y,
        }
    resp = json.dumps(result) + "\n"
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
        handle_client(conn)


if __name__ == "__main__":
    main()
