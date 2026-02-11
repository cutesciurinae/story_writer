# Gunicorn configuration file

# Number of worker processes
workers = 3

# The address to bind
bind = "0.0.0.0:13000"

# Logging level
loglevel = "info"

# Access log file
accesslog = "-"

# Error log file
errorlog = "-"