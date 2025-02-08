FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    xvfb \
    x11-apps \
    openssh-server \
    firefox \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    net-tools \
    kmod \
    linux-modules-extra-$(uname -r) && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /var/run/sshd

RUN useradd -m -s /bin/bash gui && echo "gui:password" | chpasswd && adduser gui sudo && usermod -a -G input gui

RUN python3 -m venv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH=/venv/bin:$PATH

RUN pip install --upgrade pip && pip install evdev mss
RUN pip list

ARG CACHE_BREAKER=2

COPY start.sh /start.sh
COPY input_server.py /input_server.py
COPY screenshot_server.py /screenshot_server.py
COPY 10-local.rules /etc/udev/rules.d/10-local.rules

RUN chmod +x /start.sh

ENV DISPLAY=:99

CMD ["/start.sh"]
