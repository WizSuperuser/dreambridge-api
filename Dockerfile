FROM python:3.13.2-alpine3.21

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    # curl

RUN pip install --upgrade pip

WORKDIR /root

COPY ./requirements.txt /root/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /root/requirements.txt

# RUN curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.15.1/cloud-sql-proxy.linux.amd64

# RUN chmod +x cloud-sql-proxy

# ARG INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME

# RUN ./cloud-sql-proxy $INSTANCE_CONNECTION_NAME

COPY ./app /root/app

EXPOSE 8080

CMD ["fastapi", "run", "app/api.py", "--port", "8080"]
