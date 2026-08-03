"""Gunicorn configuration for the Hotel Management Flask app.

Update the log paths if your VPS uses a different location.
"""

from multiprocessing import cpu_count

bind = "0.0.0.0:8000"
workers = (cpu_count() * 2) + 1
worker_class = "sync"
timeout = 120
keepalive = 5
accesslog = "/var/log/hotel-management/gunicorn-access.log"
errorlog = "/var/log/hotel-management/gunicorn-error.log"
loglevel = "info"
preload_app = False
capture_output = True
