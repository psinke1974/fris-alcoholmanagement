"""Beveiligingsmaatregelen die op elke response van toepassing zijn."""

import secrets
import threading
import time
from collections import defaultdict, deque

from flask import Flask, g, request

def _csp_nonce() -> str:
    if "csp_nonce" not in g:
        g.csp_nonce = secrets.token_urlsafe(16)
    return g.csp_nonce


def init_security(app: Flask) -> None:
    @app.context_processor
    def inject_nonce():
        return {"csp_nonce": _csp_nonce()}

    @app.after_request
    def set_security_headers(response):
        nonce = _csp_nonce()
        csp = "; ".join([
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "manifest-src 'self'",
            "worker-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ])
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"
        )
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        # Persoonlijke gegevens niet laten cachen door browser of proxies.
        if request.endpoint and request.endpoint != "static":
            response.headers.setdefault("Cache-Control", "no-store")
        return response


class LoginThrottle:
    """Telt mislukte inlogpogingen per sleutel binnen een tijdvenster (in-memory)."""

    def __init__(self) -> None:
        self._attempts: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, window: int, now: float) -> deque:
        attempts = self._attempts[key]
        while attempts and now - attempts[0] > window:
            attempts.popleft()
        return attempts

    def is_blocked(self, key: str, max_attempts: int, window: int) -> bool:
        with self._lock:
            return len(self._prune(key, window, time.monotonic())) >= max_attempts

    def register_failure(self, key: str, window: int) -> None:
        with self._lock:
            now = time.monotonic()
            self._prune(key, window, now).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)


login_throttle = LoginThrottle()
