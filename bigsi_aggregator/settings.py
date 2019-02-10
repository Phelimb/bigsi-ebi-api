import os

BIGSI_URLS = os.environ.get("BIGSI_URLS", "http://localhost:8000").split()
REDIS_IP = os.environ.get("REDIS_IP", "localhost")
