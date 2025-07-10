FROM python:3.9-slim

WORKDIR /app

# Install dependencies first
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy all app code last
COPY . .

EXPOSE 5000

CMD ["python", "load_balancer.py"]
