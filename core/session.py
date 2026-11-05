from __future__ import annotations

from datetime import datetime, timedelta, timezone

SESSION_MINUTES=30

def establish_session(state,user:dict)->None:
    state.user=user
    state.authenticated_at=datetime.now(timezone.utc).isoformat()
    state.session_expires_at=(datetime.now(timezone.utc)+timedelta(minutes=SESSION_MINUTES)).isoformat()

def session_is_valid(state)->bool:
    if "user" not in state or "session_expires_at" not in state:return False
    try:return datetime.now(timezone.utc)<datetime.fromisoformat(state.session_expires_at)
    except (TypeError,ValueError):return False

def clear_session(state)->None:
    for key in ("user","authenticated_at","session_expires_at","login_identity","login_password"):
        state.pop(key,None)
