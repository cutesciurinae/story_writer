# Dockerfile for story_writer
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 4999
CMD ["gunicorn", "-c", "gunicorn_config.py", "server:app"]

# Add a non-root user for security
RUN useradd -m nonrootuser
USER nonrootuser