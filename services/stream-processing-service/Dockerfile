FROM python:3.11-slim
WORKDIR /app
COPY services/stream-processing-service/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY services/stream-processing-service/app /app/app
COPY models /models
COPY artifacts /artifacts
ENV PYTHONPATH=/
ENV MODEL1_DIR=/models/anomaly_detection
ENV CAUSALOPS_ROOT=/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
