FROM python:3

ADD requirements.txt /
RUN pip install -r requirements.txt

ADD blackvue-download.py /

VOLUME [ "/data" ]

ENTRYPOINT [ "python", "./blackvue-download.py", "/data" ]