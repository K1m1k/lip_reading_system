FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/models /app/known_faces /app/logs

EXPOSE 5000 9090 8080

CMD ["python", "src/main.py"]
