FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY fl_service.py aggregator.py ./
CMD ["python", "fl_service.py"]
