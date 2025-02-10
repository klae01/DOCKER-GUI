#!/bin/bash
Xvfb $DISPLAY -screen 0 1920x1080x24 &
service ssh start
python -u /input_server.py &
python -u /screenshot_server.py &
tail -f /dev/null
