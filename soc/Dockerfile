FROM almalinux:9

WORKDIR /app

RUN dnf install -y python3.11-pip && dnf clean all

COPY ./webhook/requirements.txt ./requirements.txt
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY ./app/ ./

EXPOSE 8000 8001

CMD ["python3.11", "app.py"]
