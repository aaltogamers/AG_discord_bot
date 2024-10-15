FROM python:3.11.10-slim-bookworm

COPY requirements.txt /app/

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "alvaraalto.py"]
