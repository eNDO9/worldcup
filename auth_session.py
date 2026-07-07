"""Persistent login sessions via a signed browser cookie.

Streamlit forgets session_state on every full page load (refresh, back
button, new tab). To keep users logged in, we store an HMAC-signed token
in a browser cookie and restore the session from it on load:

  - write_cookie(): sets the cookie with a small JS snippet (Streamlit has
    no server-side cookie API).
  - read_cookie(): reads it back via st.context.cookies on the next load.

The token is `user_id:expiry:signature` — unforgeable without the signing
secret, so a tampered cookie just fails verification and shows the login.
"""
import hashlib
import hmac
import time

import streamlit as st
import streamlit.components.v1 as components

COOKIE_NAME = "wc_session"
MAX_AGE_SECONDS = 30 * 24 * 3600  # 30 days


def _secret() -> bytes:
    # Derived from the Supabase key so no new secret needs to be added to
    # the Streamlit Cloud dashboard.
    return hashlib.sha256(b"wc-session:" + st.secrets["supabase"]["key"].encode()).digest()


def make_token(user_id: str) -> str:
    expires = int(time.time()) + MAX_AGE_SECONDS
    payload = f"{user_id}:{expires}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def user_id_from_token(token: str) -> str | None:
    """Return the user id if the token is authentic and unexpired, else None."""
    try:
        user_id, expires, sig = token.split(":")
        payload = f"{user_id}:{expires}"
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected) and int(expires) > time.time():
            return user_id
    except (ValueError, AttributeError):
        pass
    return None


def read_cookie() -> str:
    return st.context.cookies.get(COOKIE_NAME) or ""


def write_cookie(user_id: str) -> None:
    token = make_token(user_id)
    components.html(f"""
        <script>
            try {{
                var p = window.parent;
                var secure = p.location.protocol === 'https:' ? '; Secure' : '';
                p.document.cookie = "{COOKIE_NAME}={token}; Max-Age={MAX_AGE_SECONDS}; Path=/; SameSite=Lax" + secure;
            }} catch (e) {{}}
        </script>
    """, height=0)


def clear_cookie() -> None:
    components.html(f"""
        <script>
            try {{
                window.parent.document.cookie = "{COOKIE_NAME}=; Max-Age=0; Path=/; SameSite=Lax";
            }} catch (e) {{}}
        </script>
    """, height=0)
