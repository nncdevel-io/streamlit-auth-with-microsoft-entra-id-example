# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

See `make help`. Use `make check` (lint + type-check) before committing.

## Architecture

`src/entra_id_auth_example/app.py` is the Streamlit entrypoint. It handles the OAuth callback
**before** `st.navigation()` (the callback is not a page), then renders shared layout and routes
to `pages/`.

## Non-obvious gotchas

- **CSRF state**: Cookie + HMAC Double Submit. `st.session_state` is lost across the OAuth
  redirect. `client_secret` doubles as the HMAC key (`handlers.py:_create_signed_state`).
- **`login()` two-stage redirect**: cookie is set via `components.html` (iframe), then
  `<meta http-equiv="refresh" content="1;...">` redirects after 1s so the cookie write completes.
  Do not collapse — iframes lack `allow-top-navigation`.
- **Multi-page uses `st.navigation()`**, not the file-based `pages/` auto-discovery. Adding a file
  under `pages/` does nothing unless it is registered in `app.py`.
- **Config loading** (`config.py:_get_config_values`):
  - `ENV=production` → reads `os.environ` only
  - otherwise → reads `.env` only (shell env vars are **ignored** in dev mode)
- **`SSL_CA_FILE`** disables `ssl.VERIFY_X509_STRICT` (Python 3.13 default). Required for corporate
  proxy CAs without the AKI extension.

## Conventions

- Source comments are written in **Japanese** — match the file's existing language when editing.
- `docs/task.md` status markers: ⏳ → 🚧 → ✅.
