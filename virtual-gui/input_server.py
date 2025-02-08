#!/usr/bin/env python3
import json
import socket
import threading

from evdev import UInput
from evdev import ecodes as e

# Global key state dictionary
key_states = {}

# Create UInput device with minimal capabilities
capabilities = {
    e.EV_KEY: list(range(0, 256)),
    e.EV_REL: [e.REL_X, e.REL_Y],
}
ui = UInput(capabilities, name="gui-virtual-input", bustype=0x03)


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
                    if op == "write":
                        # Example: {"op": "write", "type": "EV_KEY", "code": "KEY_A", "value": 1}
                        typ_str = cmd.get("type")
                        code_str = cmd.get("code")
                        value = int(cmd.get("value", 0))
                        if typ_str == "EV_KEY" and code_str:
                            key_states[code_str] = value
                        typ = (
                            getattr(e, typ_str)
                            if typ_str and hasattr(e, typ_str)
                            else None
                        )
                        code = (
                            getattr(e, code_str)
                            if code_str and hasattr(e, code_str)
                            else None
                        )
                        if typ is not None and code is not None:
                            ui.write(typ, code, value)
                    elif op == "sync":
                        ui.syn()
                    elif op == "query":
                        resp = json.dumps({"state": key_states}) + "\n"
                        conn.sendall(resp.encode("utf-8"))
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
