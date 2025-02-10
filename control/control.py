#!/usr/bin/env python3
import json
import socket
import struct
import time
from typing import Any, Dict

import paramiko


class InputController:
    def __init__(self, host: str) -> None:
        """
        Initialize the controller for a given host.

        :param host: The internal hostname or IP (as used in Docker Compose, e.g. "gui1")
        """
        self.host = host

    def _send_raw_command(self, command_dict: Dict[str, Any]) -> None:
        """
        Send a JSON command to the input server.

        :param command_dict: A dictionary representing the command to send.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, 7200))
        msg = json.dumps(command_dict) + "\n"
        s.sendall(msg.encode("utf-8"))
        s.close()
        time.sleep(0.05)

    def send_key(self, key: str) -> None:
        """
        Tap a key (simulate a press followed by a release).

        Direct tapping is allowed for alphanumeric characters and space.
        For example, 'a', 'Z', '3', or ' '.
        Any other character is processed via the Unicode input method.

        :param key: The key symbol to send.
        """
        self._send_raw_command({"op": "key", "action": "press", "key": key})
        self._send_raw_command({"op": "key", "action": "release", "key": key})

    def press_key(self, key: str) -> None:
        """Simulate a key press event."""
        self._send_raw_command({"op": "key", "action": "press", "key": key})

    def release_key(self, key: str) -> None:
        """Simulate a key release event."""
        self._send_raw_command({"op": "key", "action": "release", "key": key})

    def query_key_state(self, target="keyboard|mouse") -> Dict[str, Any]:
        """
        Query the input server for the current key states.

        :return: A dictionary of key states.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, 7200))
        msg = json.dumps(dict(op="query", target=target)) + "\n"
        s.sendall(msg.encode("utf-8"))
        resp = b""
        while b"\n" not in resp:
            resp += s.recv(1024)
        s.close()
        return json.loads(resp.decode("utf-8").strip())

    def type_unicode_char(self, ch: str) -> None:
        """
        Type a single Unicode character using the Ctrl+Shift+U sequence.

        This method sends the Unicode codepoint (in hexadecimal) as individual key events.

        :param ch: The character to type.
        """
        hex_str = format(ord(ch), "x")
        # Initiate Unicode input mode
        self._send_raw_command({"op": "key", "action": "press", "key": "Control_L"})
        self._send_raw_command({"op": "key", "action": "press", "key": "Shift_L"})
        self._send_raw_command({"op": "key", "action": "press", "key": "u"})
        self._send_raw_command({"op": "key", "action": "release", "key": "u"})
        self._send_raw_command({"op": "key", "action": "release", "key": "Control_L"})
        self._send_raw_command({"op": "key", "action": "release", "key": "Shift_L"})
        # Type each hexadecimal digit
        for digit in hex_str:
            self.send_key(digit)
        self.send_key("Return")
        time.sleep(0.1)

    def type_text(self, text: str, safe: bool = True) -> None:
        """
        Type the given text on the target system.

        If safe is True, the current key state is queried and an assertion is raised if any key
        is still pressed.

        Allowed direct characters: English letters (a–z, A–Z), digits (0–9), and space.
        All other characters are sent using the Unicode input method.

        :param text: The text to type.
        :param safe: If True, ensure no key is held down before typing.
        """
        if safe:
            state = self.query_key_state("keyboard")
            for key, value in state.get("keyboard", {}).items():
                assert int(value) == 0, f"Key {key} is pressed (state={value})."
        for ch in text:
            if ch.isalnum():
                self.send_key(ch)
            else:
                self.type_unicode_char(ch)
            time.sleep(0.1)

    def _mouse_move(self, **kwargs: int) -> None:
        cmd = {
            "op": "mouse",
            "action": "move",
            **{k: v for k, v in kwargs.items() if v is not None},
        }
        self._send_raw_command(cmd)

    def mouse_move_abs(self, x: int = None, y: int = None) -> None:
        self._mouse_move(x=x, y=y)

    def mouse_move_rel(self, dx: int = None, dy: int = None) -> None:
        self._mouse_move(dx=dx, dy=dy)

    def mouse_click(self, button: str = "left") -> None:
        """
        Simulate a mouse click (press followed by release).

        :param button: The mouse button to click ("left", "middle", or "right").
        """
        self._send_raw_command(
            {"op": "mouse", "action": "click", "button": button, "state": "press"}
        )
        self._send_raw_command(
            {"op": "mouse", "action": "click", "button": button, "state": "release"}
        )

    def mouse_scroll(self, direction: str = "up", amount: int = 1) -> None:
        """
        Scroll the mouse in the specified direction.

        Allowed directions: "up", "down", "left", "right".

        :param direction: The scroll direction.
        :param amount: Number of scroll units.
        """
        cmd = {
            "op": "mouse",
            "action": "scroll",
            "direction": direction,
            "amount": amount,
        }
        self._send_raw_command(cmd)

    def ssh_run(self, command: str) -> None:
        """
        Run a command on the host via SSH.

        Assumes username "gui" and password "password".

        :param command: The command to execute.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, port=22, username="gui", password="password")
        ssh.exec_command(command)
        time.sleep(1)
        ssh.close()

    def get_screenshot(self, filename: str) -> None:
        """
        Request a screenshot from the screenshot server (port 7300) and save it to a file.

        :param filename: Path to save the screenshot.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, 7300))
        s.sendall(b"GET\n")
        header = b""
        while len(header) < 12:
            header += s.recv(12 - len(header))
        width, height, channels = struct.unpack("!III", header)
        data_size = width * height * channels
        raw_data = b""
        while len(raw_data) < data_size:
            raw_data += s.recv(data_size - len(raw_data))
        s.close()
        with open(filename, "wb") as f:
            f.write(header)
            f.write(raw_data)
        print(f"{self.host}: Screenshot saved to {filename}")


def main() -> None:
    gui1 = InputController("gui1")
    gui2 = InputController("gui2")

    time.sleep(10)
    print("Processing gui1")
    gui1.ssh_run("DISPLAY=:99 firefox google.com &")
    time.sleep(5)
    gui1.get_screenshot("/shared/gui1_google.raw")
    gui1.type_text("goose goose duck", safe=True)
    gui1.get_screenshot("/shared/gui1_type.raw")
    gui1.send_key("Return")
    time.sleep(5)
    gui1.get_screenshot("/shared/gui1_search.raw")
    gui1.send_key("F11")
    time.sleep(5)
    gui1.get_screenshot("/shared/gui1_full.raw")

    for i in range(100):
        gui1.get_screenshot("/shared/gui1_screenshot.raw")
        print(time.time())

    print("Processing gui2")
    gui2.ssh_run("DISPLAY=:99 firefox naver.com &")
    time.sleep(5)
    gui2.get_screenshot("/shared/gui2_naver.raw")
    time.sleep(5)
    gui2.mouse_move_abs(500, 500)
    gui2.mouse_click()
    time.sleep(5)
    gui2.get_screenshot("/shared/gui2_mouse.raw")
    for i in range(5):
        gui2.mouse_scroll("down", 1)
        gui2.get_screenshot(f"/shared/gui2_scroll_{i}.raw")

    print("Processing gui2 - diep.io")
    gui2.ssh_run("DISPLAY=:99 firefox diep.io &")
    for i in range(100):
        gui2.get_screenshot(f"/shared/gui2_diep/{i}.raw")
        print(time.time())


if __name__ == "__main__":
    main()
