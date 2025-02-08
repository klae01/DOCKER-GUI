#!/usr/bin/env python3
import socket
import struct

from mss import mss


def handle_client(conn):
    try:
        data = conn.recv(1024).decode("utf-8").strip()
        if data == "GET":
            with mss() as sct:
                monitor = sct.monitors[0]
                img = sct.grab(monitor)
                raw = img.rgb
                width, height, channels = img.width, img.height, 3
                header = struct.pack("!III", width, height, channels)
                conn.sendall(header + raw)
    except Exception as ex:
        print("Screenshot error:", ex)
    finally:
        conn.close()


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 7300))
    s.listen(5)
    print("Screenshot server running on port 7300")
    while True:
        conn, addr = s.accept()
        handle_client(conn)


if __name__ == "__main__":
    main()
