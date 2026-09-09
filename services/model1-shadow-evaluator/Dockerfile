FROM python:3.11-slim
WORKDIR /app
RUN pip install torch numpy confluent_kafka
# Copy strictly what's needed statically since volume mapping fails
COPY services/model1-shadow-evaluator/main.py /app/main.py
COPY models /models
CMD ["python", "/app/main.py"]
