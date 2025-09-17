FROM python:3.9-slim

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ml/code

COPY sagemaker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY src/recommender/rf_train.py .
COPY src/recommender/pm_train.py .
COPY src/recommender/spm_train.py .
COPY src/recommender/inference.py .
COPY src/recommender/rf_inference.py .
COPY src/recommender/pm_inference.py .
COPY src/recommender/spm_inference.py .
COPY src/recommender/subjects.py .
COPY src/recommender/entrypoint.py .

ENV SAGEMAKER_PROGRAM=entrypoint.py
EXPOSE 8080

ENTRYPOINT ["python", "entrypoint.py"]

