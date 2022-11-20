# Author: Claire Gregg
FROM python:latest

ADD controller/controller.py /controller/
COPY lib.py /controller/

WORKDIR /controller/

ENTRYPOINT ["python3", "-u", "controller.py"]