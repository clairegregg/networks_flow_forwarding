# Author: Claire Gregg
FROM python:latest

ADD interactive_client/interactive_client.py /client/
COPY lib.py /client/


WORKDIR /client/

ENTRYPOINT ["python3", "-u", "interactive_client.py"]