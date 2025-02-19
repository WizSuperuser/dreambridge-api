FROM python:3.13.2-alpine3.21

WORKDIR /root

COPY ./requirements.txt /root/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /root/requirements.txt

COPY ./app /root/app

EXPOSE 8080

CMD ["fastapi", "run", "app/api.py", "--port", "8080"]
