# Author: Claire Gregg

FROM python:latest

ADD server/server.py /server/
COPY lib.py /server/

WORKDIR /server/

EXPOSE 54321/udp

ENTRYPOINT ["python3", "-u", "server.py"]