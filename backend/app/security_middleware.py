# ============================================
# SECURITY MIDDLEWARES - BL Genius
# Headers de sécurité + Validation
# ============================================

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import re
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Ajoute les headers de sécurité recommandés
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Empêche le MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Protection contre le clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Protection XSS (navigateurs anciens)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (anciennement Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "vr=()"
        )

        # Cache Control pour les données sensibles
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Valide les requêtes entrantes
    """
    async def dispatch(self, request: Request, call_next):
        # Vérifier la taille du body (protection contre les attaques par déni de service)
        content_length = request.headers.get("content-length")
        if content_length:
            max_size = 500 * 1024 * 1024  # 500 MB
            if int(content_length) > max_size:
                raise HTTPException(413, "Request entity too large")

        # Vérifier les headers suspects
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 1000:
            logger.warning(f"Suspicious User-Agent length: {len(user_agent)}")
            raise HTTPException(400, "Invalid User-Agent")

        # Vérifier les caractères dans l'URL (prévention XSS/Injection)
        path = request.url.path
        if re.search(r'[<>:"|?*\x00-\x1f]', path):
            raise HTTPException(400, "Invalid characters in URL")

        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Log les requêtes importantes pour l'audit
    """
    async def dispatch(self, request: Request, call_next):
        # Routes sensibles à logger
        sensitive_routes = ["/upload", "/analyze", "/auth/login", "/auth/register"]

        should_log = any(request.url.path.startswith(route) for route in sensitive_routes)

        if should_log:
            logger.info({
                "event": "REQUEST",
                "method": request.method,
                "path": request.url.path,
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "")[:200],
                "timestamp": str(datetime.utcnow())
            })

        response = await call_next(request)

        if should_log:
            logger.info({
                "event": "RESPONSE",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "timestamp": str(datetime.utcnow())
            })

        return response


from datetime import datetime
