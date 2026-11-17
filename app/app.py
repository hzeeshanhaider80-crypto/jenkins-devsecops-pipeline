"""A small Flask web app that counts visits using Redis."""
import os
import socket

import redis
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Settings come from environment variables (set in docker-compose.yml).
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
APP_VERSION = os.getenv("APP_VERSION", "local")

# Connection to the Redis container. Short timeout so the page never hangs.
cache = redis.Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2,
                    decode_responses=True)


def get_visits():
    """Add 1 to the visit counter in Redis and return it (None if Redis is down)."""
    try:
        return cache.incr("visits")
    except redis.exceptions.RedisError:
        return None


@app.route("/")
def home():
    return render_template(
        "index.html",
        visits=get_visits(),
        version=APP_VERSION,
        container=socket.gethostname(),
    )


@app.route("/health")
def health():
    # Used by Docker, Nginx and the deploy script. Must NOT depend on Redis.
    return jsonify(status="ok")


@app.route("/api/info")
def info():
    return jsonify(version=APP_VERSION, container=socket.gethostname())
