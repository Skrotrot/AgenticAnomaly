FROM almalinux:9

ENV PATH="/root/.opencode/bin:${PATH}"
WORKDIR /app
ARG OPENCODE_VERSION=1.17.7

RUN dnf install -y python3-pip && dnf clean all

RUN curl -fsSL https://opencode.ai/install | bash -s -- --version "${OPENCODE_VERSION}" --no-modify-path

COPY ./opencode/ /root/.config/opencode/

COPY ./webhook/requirements.txt ./requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY ./webhook/ ./

EXPOSE 8000

CMD ["python3", "app.py"]
