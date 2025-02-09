FROM python:3.10-slim
RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    python3 \
    python3-pip \
    python3-venv && \
    rm -rf /var/lib/apt/lists/*
RUN python -m venv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH=/venv/bin:$PATH
RUN pip install --upgrade pip && pip install paramiko

COPY control.py /control.py

CMD ["python", "-u", "/control.py"]