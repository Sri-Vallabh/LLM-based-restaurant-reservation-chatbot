

# Use an official Python runtime as a parent image
FROM python:3.11-slim


# Set the working directory in the container
WORKDIR /app

ENV HF_HOME=/data/hf_cache
ENV TRANSFORMERS_CACHE=/data/hf_cache/transformers
ENV HF_DATASETS_CACHE=/data/hf_cache/datasets
ENV HF_HUB_CACHE=/data/hf_cache/hub

RUN mkdir -p /data/hf_cache/transformers /data/hf_cache/datasets /data/hf_cache/hub && chmod -R 777 /data/hf_cache

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
