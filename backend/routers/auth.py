"""
Firebase JWT verification middleware.
Verifies Bearer tokens and attaches user_id, email, role to request.state.
"""
import logging
from typing import List

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

import google.auth.transport.requests
from google.oauth2 import id_token
import os

logger = logging.getLogger(__name__)

# Paths that bypass auth entirely
EXEMPT_PATHS: List[str] = ["/healthz", "/readyz", "/docs", "/openapi.json", "/redoc"]

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")


class AuthMiddleware(BaseHTTPMiddleware):
    """Verifies Firebase JWT tokens on all requests except exempt paths."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Exempt paths bypass auth
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        # OPTIONS requests bypass auth (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.replace("Bearer ", "")

        try:
            # Verify Firebase ID token
            decoded = id_token.verify_firebase_token(
                token,
                google.auth.transport.requests.Request(),
                audience=FIREBASE_PROJECT_ID,
            )

            # Attach user info to request state
            request.state.user_id = decoded.get("uid", decoded.get("sub", ""))
            request.state.email = decoded.get("email", "")
            request.state.role = decoded.get("role", "officer")
            request.state.officer_id = decoded.get("uid", decoded.get("sub", ""))

        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        return await call_next(request)
