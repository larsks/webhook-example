FROM docker.io/python:3

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--log-file", "-", "--access-logfile", "-", "app:app"]
