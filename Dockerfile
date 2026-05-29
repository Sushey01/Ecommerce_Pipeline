FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY app/model.pkl ./

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app.app:app"]