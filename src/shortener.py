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