# Dockerfile
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# port FastAPI runs on
EXPOSE 8000

# Start the server
# --host 0.0.0.0 makes it accessible outside the container
# --reload is OFF in production (remove for prod builds)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]