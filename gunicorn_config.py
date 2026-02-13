# gunicorn_config.py

bind = "0.0.0.0:4999"

# CRITICAL: Use eventlet for SocketIO. 
# This allows one worker to handle hundreds of concurrent connections.
worker_class = "eventlet"

# CRITICAL: Without a session manager (like Redis), you MUST use 1 worker.
# If you use > 1, SocketIO messages will get lost between processes.
workers = 1

# Logging configuration
accesslog = "-"
errorlog = "-"

# Keep-alive settings for WebSockets
keepalive = 5
timeout = 120

# Trust the Docker proxy headers
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
