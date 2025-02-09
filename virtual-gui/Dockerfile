FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    xvfb \
    x11-apps \
    openssh-server \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    net-tools \
    wget && \
    rm -rf /var/lib/apt/lists/*

RUN wget "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" -O /tmp/firefox.tar.xz && \
    cd /tmp && \
    tar -xf firefox.tar.xz && \
    mv firefox /opt && \
    ln -s /opt/firefox/firefox /usr/local/bin/firefox && \
    rm -rf /tmp/firefox*
RUN mkdir /var/run/sshd

RUN apt-get update && apt-get install -y \
    libgtk-3-dev \
    libasound2-dev && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash gui && echo "gui:password" | chpasswd && adduser gui sudo

RUN python3 -m venv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH=/venv/bin:$PATH
ENV DISPLAY=:99

RUN pip install --upgrade pip && pip install python-xlib mss

ARG CACHE_BREAKER=2

COPY start.sh /start.sh
COPY input_server.py /input_server.py
COPY screenshot_server.py /screenshot_server.py

RUN chmod +x /start.sh

CMD ["/start.sh"]
