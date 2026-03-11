FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY app.py .

RUN pip install --no-cache-dir flask flask-cors agntcy-dir==1.0.0 requests

USER 1000:1000

CMD ["python", "app.py"]
