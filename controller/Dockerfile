# Author: Claire Gregg
FROM python:latest

ADD controller/controller.py /controller/
#COPY forwarding_service.py /employee/

WORKDIR /controller/

ENTRYPOINT ["python3", "-u", "controller.py"]