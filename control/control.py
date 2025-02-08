#!/usr/bin/env python3
import json
import socket
import struct
import time

import paramiko


def send_raw_command(host, op, type=None, code=None, value=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, 7200))
    msg = json.dumps(dict(op=op, type=type, code=code, value=value)) + "\n"
    s.sendall(msg.encode("utf-8"))
    s.close()


def send_key(host, keycode):
    send_raw_command(host, op="write", type="EV_KEY", code=keycode, value=1)
    send_raw_command(host, op="sync")
    send_raw_command(host, op="write", type="EV_KEY", code=keycode, value=0)
    send_raw_command(host, op="sync")


ascii_mapping = {ch: "KEY_" + ch.upper() for ch in "abcdefghijklmnopqrstuvwxyz"}
ascii_mapping[" "] = "KEY_SPACE"
digit_mapping = {d: "KEY_" + d for d in "0123456789"}
hex_mapping = {ch: "KEY_" + ch.upper() for ch in "0123456789abcdef"}


def query_key_state(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, 7200))
    s.sendall(b'{"op": "query"}\n')
    resp = b""
    while b"\n" not in resp:
        resp += s.recv(1024)
    s.close()
    return json.loads(resp.decode("utf-8").strip())


def type_unicode_char(host, ch):
    hex_str = format(ord(ch), "x")
    send_raw_command(host, op="write", type="EV_KEY", code="KEY_LEFTCTRL", value=1)
    send_raw_command(host, op="write", type="EV_KEY", code="KEY_LEFTSHIFT", value=1)
    send_raw_command(host, op="write", type="EV_KEY", code="KEY_U", value=1)
    send_raw_command(host, op="sync")
    send_raw_command(host, op="write", type="EV_KEY", code="KEY_U", value=0)
    send_raw_command(host, op="sync")
    send_raw_command(host, op="write", type="EV_KEY", code="KEY_LEFTCTRL", value=0)
    send_raw_command(host, op="write", type="EV_KEY", code="KEY_LEFTSHIFT", value=0)
    send_raw_command(host, op="sync")
    time.sleep(0.05)
    for digit in hex_str:
        key_for_digit = hex_mapping.get(digit.lower())
        if not key_for_digit:
            raise ValueError(f"Unsupported hex digit: {digit}")
        send_key(host, key_for_digit)
        time.sleep(0.05)
    send_key(host, "KEY_ENTER")
    time.sleep(0.1)


def type_text(host, text, safe=True):
    if safe:
        state = query_key_state(host)
        for key, value in state.get("state", {}).items():
            assert int(value) == 0, f"Key {key} is pressed (state={value})."
    for ch in text:
        if ch.lower() in ascii_mapping:
            send_key(host, ascii_mapping[ch.lower()])
        elif ch in digit_mapping:
            send_key(host, digit_mapping[ch])
        else:
            type_unicode_char(host, ch)
        time.sleep(0.1)


def ssh_run(host, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=22, username="gui", password="password")
    ssh.exec_command(command)
    time.sleep(1)
    ssh.close()


def get_screenshot(host, filename):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, 7300))
    s.sendall(b"GET\n")
    header = b""
    while len(header) < 12:
        header += s.recv(12 - len(header))
    width, height, channels = struct.unpack("!III", header)
    data_size = width * height * channels
    raw_data = b""
    while len(raw_data) < data_size:
        raw_data += s.recv(min(4096, data_size - len(raw_data)))
    s.close()
    with open(filename, "wb") as f:
        f.write(header)
        f.write(raw_data)
    print(f"{host}: Screenshot saved to {filename}")


def main():
    gui1 = "gui1"
    gui2 = "gui2"

    time.sleep(10)
    print("Processing gui1")
    ssh_run(gui1, "firefox google.com &")
    time.sleep(5)
    get_screenshot(gui1, "gui1_google.raw")
    type_text(gui1, "goose goose duck", safe=True)
    time.sleep(5)
    get_screenshot(gui1, "gui1_search.raw")

    print("Processing gui2")
    ssh_run(gui2, "firefox naver.com &")
    time.sleep(5)
    get_screenshot(gui2, "gui2_naver.raw")
    for _ in range(3):
        send_key(gui2, "KEY_END")
        time.sleep(1)
    get_screenshot(gui2, "gui2_scroll.raw")


if __name__ == "__main__":
    main()
