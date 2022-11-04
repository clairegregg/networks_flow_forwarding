# Author: Claire Gregg
FROM python:latest

ADD client/client.py /client/
#COPY forwarding_service.py /employee/

WORKDIR /client/

ENTRYPOINT ["python3", "-u", "client.py"]