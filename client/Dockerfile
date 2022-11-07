# Author: Claire Gregg
FROM python:latest

ADD client/client.py /client/
COPY lib.py /client/


WORKDIR /client/

ENTRYPOINT ["python3", "-u", "client.py"]