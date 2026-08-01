FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Hugging Face Spaces routes traffic to port 7860 by default)
ENV PORT=7860
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]
