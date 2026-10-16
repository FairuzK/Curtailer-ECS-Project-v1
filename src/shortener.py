# Imports, constants and schema definition for the URL shortener service.
import os
import secrets
import sqlite3
import string
from contextlib import closing
from urllib.parse import urlparse

from flask import Flask, abort, g, jsonify, redirect, render_template, request
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

# The app Factory and database connection management. 
# The app is created by the WSGI server (gunicorn) and the Flask test client. 
#  The database connection is created on demand and closed at the end of each request. 
# The database is initialized if it does not exist yet.

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        DB_PATH=os.environ.get("DB_PATH", "data/urls.db"),
        APP_VERSION=os.environ.get("APP_VERSION", "dev"),
    )
    if test_config:
        app.config.update(test_config)

    # The ALB terminates TLS and sets X-Forwarded-* headers. Trust exactly one hop
    # so request.host_url builds correct https:// short links.

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

    @app.get("/")
    def index():
        return render_template("index.html")

# The API endpoints. The shortener service is a single-page app, so the API is not versioned.
# The 2 core endpoints are POST /api/shorten to create a new short link and GET /<code> to follow a short link.

    @app.post("/api/shorten")
    def shorten():
        payload = request.get_json(silent=True)
        url = (payload.get("url") or "").strip() if isinstance(payload, dict) else ""
        error = validate_url(url, request.host)
        if error:
            return jsonify(error=error), 400

        db = get_db()
        for _ in range(5):  # retry on the (very unlikely) code collision
            code = new_code()
            try:
                db.execute("INSERT INTO links (code, original_url) VALUES (?, ?)", (code, url))
                db.commit()
                break
            except sqlite3.IntegrityError:
                continue
        else:
            return jsonify(error="could not allocate a short code"), 500

        return jsonify(code=code, original_url=url, short_url=f"{request.host_url}{code}"), 201
    
# The Operartional endpoints. These are used by the container health check, ALB target group and CI.

    @app.get("/api/links/<code>")
    def link_stats(code):
        row = get_db().execute(
            "SELECT code, original_url, clicks, created_at FROM links WHERE code = ?", (code,)
        ).fetchone()
        if row is None:
            abort(404)
        return jsonify(dict(row))

    @app.get("/health")
    def health():
        """Used by the container health check, ALB target group and CI."""
        try:
            get_db().execute("SELECT 1").fetchone()
        except sqlite3.Error:
            return jsonify(status="unhealthy"), 503
        return jsonify(status="ok")

    @app.get("/version")
    def version():
        """CI polls this to prove the NEW image is the one serving traffic."""
        return jsonify(version=app.config["APP_VERSION"])

    @app.get("/<code>")
    def follow(code):
        if len(code) != CODE_LENGTH or any(c not in ALPHABET for c in code):
            abort(404)
        db = get_db()
        row = db.execute("SELECT original_url FROM links WHERE code = ?", (code,)).fetchone()
        if row is None:
            abort(404)
        db.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
        db.commit()
        return redirect(row["original_url"], code=302)

    return app
