FROM stream-processing-service:latest
WORKDIR /app
COPY services/model1-shadow-evaluator/main.py /app/main.py
COPY models /models
CMD ["python", "/app/main.py"]
