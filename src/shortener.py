import os
import secrets
import sqlite3

import string
from contextlib import closing
from urllib.parse import urlparse

from flask import Flask, abort, g, jsonify, redirect, request
from werkzeug.middleware.proxy_fix import ProxyFix

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
MAX_URL_LENGTH = 2048

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    code         TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    clicks       INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def new_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def validate_url(url: str, own_host: str):
    """Return an error string, or None if the URL is acceptable."""
    if not url:
        return "url is required"
    if len(url) > MAX_URL_LENGTH:
        return "url is too long"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "url must start with http:// or https://"
    if parsed.netloc.lower() == own_host.lower():
        return "refusing to shorten a link to this service"
    return None

# App factory and database setup
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        DB_PATH=os.environ.get("DB_PATH", "data/urls.db"),
        APP_VERSION=os.environ.get("APP_VERSION", "dev"),
    )
    if test_config:
        app.config.update(test_config)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    os.makedirs(os.path.dirname(os.path.abspath(app.config["DB_PATH"])), exist_ok=True)
    with closing(sqlite3.connect(app.config["DB_PATH"])) as conn:
        conn.executescript(SCHEMA)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"], timeout=10)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()