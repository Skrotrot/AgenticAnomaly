FROM almalinux:9

WORKDIR /app

RUN dnf install -y python3-pip && dnf clean all

COPY requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY app.py ./

EXPOSE 8443 8444

CMD ["python3", "app.py"]
