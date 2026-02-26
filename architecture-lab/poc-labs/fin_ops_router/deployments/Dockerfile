# Use Python 3.11 slim
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src folder
COPY src ./src

# Add src to PYTHONPATH so Python can find finops_llm_router
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8001

# Run the app
CMD ["python", "src/main.py"]
