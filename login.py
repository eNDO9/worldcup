import streamlit as st
import streamlit.components.v1 as components
import db


def render():
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    _, col_m, _ = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 2rem;">
            <div style="font-size:3.5rem;line-height:1;">⚽</div>
            <h1 style="margin:0.6rem 0 0.3rem;font-size:2.2rem;font-weight:700;color:#f1f5f9;">
                World Cup Survivor
            </h1>
            <p style="color:#94a3b8;font-size:1rem;margin:0;">
                Pick one team per round &nbsp;·&nbsp; Never reuse &nbsp;·&nbsp; Last one standing wins
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_mode == "login":
            with st.form("login"):
                st.text_input("Email", key="li_user", placeholder="you@example.com")
                st.text_input("Password", type="password", key="li_pass", placeholder="Your password")
                if st.form_submit_button("Log In", use_container_width=True):
                    u, p = st.session_state.li_user, st.session_state.li_pass
                    if u and p:
                        user = db.login_user(u, p)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                    else:
                        st.warning("Please fill in both fields.")

            st.markdown('<p style="text-align:center;margin-top:0.6rem;color:#94a3b8;font-size:0.8rem;">'
                        'Forgot your password? Message the pool admin to reset it.</p>',
                        unsafe_allow_html=True)
            st.markdown('<p style="text-align:center;margin-top:1rem;color:#94a3b8;font-size:0.9rem;">Don\'t have an account?</p>',
                        unsafe_allow_html=True)
            if st.button("Create an account →", use_container_width=True, key="go_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            with st.form("signup"):
                st.text_input("Email", key="su_user", placeholder="you@example.com")
                st.text_input("Password", type="password", key="su_pass", placeholder="At least 6 characters")
                st.text_input("Confirm password", type="password", key="su_conf", placeholder="Repeat password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    u, p, c = st.session_state.su_user, st.session_state.su_pass, st.session_state.su_conf
                    if not (u and p and c):
                        st.warning("Please fill in all fields.")
                    elif "@" not in u:
                        st.error("Please enter a valid email address.")
                    elif p != c:
                        st.error("Passwords don't match.")
                    elif len(p) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        user = db.create_user(u, p)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("An account with that email already exists.")

            st.markdown('<p style="text-align:center;margin-top:1rem;color:#94a3b8;font-size:0.9rem;">Already have an account?</p>',
                        unsafe_allow_html=True)
            if st.button("← Back to Log In", use_container_width=True, key="go_login"):
                st.session_state.auth_mode = "login"
                st.rerun()

    components.html("""
    <script>
    (function() {
      function patch() {
        try {
          var doc = window.parent.document;
          var email = doc.querySelector('input[aria-label="Email"]');
          if (email) { email.autocomplete = 'email'; email.name = 'email'; }
          var hasConfirm = !!doc.querySelector('input[aria-label="Confirm password"]');
          var pw = doc.querySelector('input[aria-label="Password"]');
          if (pw) { pw.autocomplete = hasConfirm ? 'new-password' : 'current-password'; pw.name = 'password'; }
          var conf = doc.querySelector('input[aria-label="Confirm password"]');
          if (conf) { conf.autocomplete = 'new-password'; conf.name = 'confirm-password'; }
          return !!(email || pw);
        } catch(e) { return false; }
      }
      if (!patch()) {
        try {
          var obs = new MutationObserver(function() { if (patch()) { obs.disconnect(); } });
          obs.observe(window.parent.document.body, { childList: true, subtree: true });
          setTimeout(function() { obs.disconnect(); }, 8000);
        } catch(e) {
          setTimeout(patch, 500);
          setTimeout(patch, 1500);
          setTimeout(patch, 3000);
        }
      }
    })();
    </script>
    """, height=0)
