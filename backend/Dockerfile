
FROM python:3.10-alpine

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app/api-server
ENV PYTHONPATH "${PYTHONPATH}:/app/api-server"

CMD ["uvicorn", "api-server.server:app", "--host", "0.0.0.0", "--port", "80"]