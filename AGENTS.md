# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Commands

See `make help`. Use `make check` (lint + type-check) before committing.

## Architecture

`streamlit run` targets `src/entra_id_auth_example/server.py`, which builds an `st.App` for the
script `app.py`. `server.py` passes the auth config as `st.secrets["auth"]` and adds the
`/callback` forwarding route. `app.py` renders shared layout and routes to `pages/`.
Authentication is Streamlit's built-in `st.login()` / `st.logout()` / `st.user`.

## Non-obvious gotchas

- **Callback path**: `st.login()` only handles `/oauth2callback` (fixed in Streamlit). The Entra ID
  app registration keeps `/callback`, so `callback.py` forwards `/callback?...` to
  `/oauth2callback?...`. The token exchange still sends `/callback` as `redirect_uri` (Authlib
  reuses the value from the authorize request). Streamlit logs "Redirect URI does not end with
  /oauth2callback" at startup; this is expected.
- **Config is passed as secrets**: `config.py:AuthConfig.to_streamlit_secrets` builds the `[auth]`
  section; there is no `.streamlit/secrets.toml`. `AUTH_COOKIE_SECRET` is required.
- **`st.user` reads the auth cookie only at session start.** Call `st.login()` / `st.logout()` to
  update it within a running session.
- **Multi-page uses `st.navigation()`**, not the file-based `pages/` auto-discovery. Adding a file
  under `pages/` does nothing unless it is registered in `app.py`.
- **Config loading** (`config.py:_get_config_values`):
  - `ENV=production` → reads `os.environ` only
  - otherwise → reads `.env` only (shell env vars are **ignored** in dev mode)
- **`SSL_CA_FILE`** is passed to httpx (used by Authlib) as `client_kwargs.verify`. An
  `ssl.SSLContext` cannot be passed through secrets, so `ssl.VERIFY_X509_STRICT` (Python 3.13
  default) stays enabled.

## Conventions

- Source comments are written in **Japanese** — match the file's existing language when editing.
- `docs/task.md` status markers: ⏳ → 🚧 → ✅.
