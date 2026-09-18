from dataclasses import dataclass
import os

import requests
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None


def public_auth_config() -> dict[str, str]:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_anon_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured.")
    return {"url": supabase_url.rstrip("/"), "anon_key": supabase_anon_key}


def current_user(credentials: HTTPAuthorizationCredentials | None) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required.")
    config = public_auth_config()
    response = requests.get(
        f"{config['url']}/auth/v1/user",
        headers={"apikey": config["anon_key"], "Authorization": f"Bearer {credentials.credentials}"},
        timeout=10,
    )
    if not response.ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired. Please sign in again.")
    payload = response.json()
    return AuthenticatedUser(id=payload["id"], email=payload.get("email"))