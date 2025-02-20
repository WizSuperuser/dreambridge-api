FROM python:3.13.2-alpine3.21

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

RUN pip install --upgrade pip

WORKDIR /root

COPY ./requirements.txt /root/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /root/requirements.txt

COPY ./app /root/app

EXPOSE 8080

CMD ["fastapi", "run", "app/api.py", "--port", "8080"]
