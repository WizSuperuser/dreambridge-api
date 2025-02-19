FROM python:3.13.2-alpine3.21

WORKDIR /root

COPY ./requirements.txt /root/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /root/requirements.txt

COPY ./app /root/app

CMD ["fastapi", "run", "app/api.py", "--port", "80"]
