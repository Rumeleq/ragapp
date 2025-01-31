FROM python:3.13-slim
LABEL authors="wiktor"

# Select container's working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*
RUN pip install setuptools

COPY requirements.txt .

# Install python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "main.py"]