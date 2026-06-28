# Claude Instructions for worldcup

## Git / GitHub
- **Push changes automatically** after every meaningful commit — do not ask for confirmation.
- Always use the personal GitHub account (eNDO9), never the organizational account (ndo@isdglobal.org).

## Project stack
- Streamlit frontend — entry point is `app.py`
- Supabase backend — client initialized in `supabase_client.py`
- Credentials live in `.streamlit/secrets.toml` (gitignored, never commit)

## Streamlit Cloud
- Account: endo9 (linked to personal GitHub)
- Secrets must be re-entered in the Streamlit Cloud dashboard when new keys are added
