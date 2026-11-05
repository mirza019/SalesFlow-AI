from __future__ import annotations
import hmac
import hashlib
import time
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from .database import execute, query

_hasher=PasswordHasher()
_attempts:dict[str,list[float]]={}
MAX_ATTEMPTS=5
ATTEMPT_WINDOW_SECONDS=60

PERMISSIONS={
 "Administrator":{"view","build_workflow","activate_workflow","request_change","approve_change","run_rpa","view_audit"},
 "Sales Manager":{"view","build_workflow","activate_workflow","request_change","approve_change","run_rpa","view_audit"},
 "Citizen Developer":{"view","build_workflow","request_change"},
}

def hash_password(password:str)->str:
    return _hasher.hash(password)

def _identity(value:str)->str:
    identity=value.strip().lower()
    if identity.endswith("@salesops.local"):
        identity=identity.split("@",1)[0]
    return identity

def _throttled(identity:str)->bool:
    now=time.monotonic()
    attempts=[stamp for stamp in _attempts.get(identity,[]) if now-stamp<ATTEMPT_WINDOW_SECONDS]
    _attempts[identity]=attempts
    return len(attempts)>=MAX_ATTEMPTS

def authenticate(username:str,password:str)->dict|None:
    username=_identity(username)
    if not username or not password or _throttled(username):return None
    rows=query("SELECT username,display_name,role,password_hash FROM users WHERE username=? AND active=1",(username,))
    if not rows:
        _attempts.setdefault(username,[]).append(time.monotonic());return None
    user=rows[0]
    stored=user.pop("password_hash")
    try:
        valid=_hasher.verify(stored,password)
        if valid and _hasher.check_needs_rehash(stored):
            execute("UPDATE users SET password_hash=? WHERE username=?",(hash_password(password),username))
    except InvalidHashError:
        # One-time upgrade path for databases created by earlier portfolio builds.
        valid=hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(),stored)
        if valid:execute("UPDATE users SET password_hash=? WHERE username=?",(hash_password(password),username))
    except VerifyMismatchError:
        valid=False
    if not valid:
        _attempts.setdefault(username,[]).append(time.monotonic());return None
    _attempts.pop(username,None)
    return user

def require_permission(user:dict,permission:str)->None:
    if not user or permission not in PERMISSIONS.get(user.get("role"),set()):
        raise PermissionError(f"Role is not permitted to {permission.replace('_',' ')}")

