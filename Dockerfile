FROM kalilinux/kali-rolling:latest

RUN apt-get update && \
    apt-get install -y git python3-pip python3-venv figlet sudo boxes php curl xdotool wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /root/hackingtool

COPY requirements.txt ./

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir boxes flask lolcat requests -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

RUN true && echo "/root/hackingtool/" > /home/hackingtoolpath.txt

EXPOSE 1-65535

ENTRYPOINT ["python3", "/root/hackingtool/hackingtool.py"]
