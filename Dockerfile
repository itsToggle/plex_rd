FROM python:3

RUN apt-get update && apt-get install -y vim less

ADD . / ./

RUN pip install -r requirements.txt

ENV TERM=xterm

CMD [ "python", "./main.py", "--config-dir", "config", "-e", "TERM=xterm"]
