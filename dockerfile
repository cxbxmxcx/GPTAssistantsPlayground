FROM python:3.11-slim

WORKDIR /app

# (Optional) Install system-level dependencies here if needed
# RUN apt-get update && apt-get install -y <dependencies> && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "main.py"]
