FROM python:3.9-slim

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ml/code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/recommender/asb_recommender.py .

CMD ["python", "asb_recommender.py"]

