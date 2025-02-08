#!/bin/bash
modprobe uinput
if [ ! -c /dev/uinput ]; then
    mknod /dev/uinput c 10 223
    chown root:input /dev/uinput
    chmod +0666 /dev/uinput
fi
sudo udevadm control --reload 
sudo udevadm trigger

Xvfb $DISPLAY -screen 0 1920x1080x24 &
sleep 2
service ssh start
su - gui -c "/venv/bin/python /input_server.py" &
su - gui -c "/venv/bin/python /screenshot_server.py" &
tail -f /dev/null
