# Author: Claire Gregg

FROM python:latest

ADD forwarders/forwarder.py /forwarder/
COPY lib.py /forwarder/

WORKDIR /forwarder/
EXPOSE 54321/udp

ENTRYPOINT ["python3", "-u", "forwarder.py"]