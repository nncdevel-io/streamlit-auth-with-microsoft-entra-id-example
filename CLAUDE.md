# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install-dev  # Install dependencies
make run          # Run application
make test         # Run tests
make check        # Run lint + type-check
```

## Architecture

`app.py` is the entrypoint/router using `st.navigation()`. It handles OAuth callbacks, shared layout, and page routing.

```text
src/entra_id_auth_example/
├── config.py     # AuthConfig, env loading
├── client.py     # EntraAuthClient (MSAL wrapper)
├── handlers.py   # login, logout, handle_callback, require_auth, UI components
├── app.py        # Entrypoint: router + shared layout + OAuth callback
└── pages/        # Page content (no set_page_config or shared layout calls)
    ├── home.py       # Home page (login / user info)
    ├── about.py      # About page (public)
    ├── dashboard.py  # Dashboard (auth required)
    └── profile.py    # Profile (auth required)
```

## Key Design Decisions

- **CSRF protection**: Cookie + HMAC Double Submit pattern (not session_state, which is lost across redirects)
- **Multi-page**: `st.navigation()` API (not file-based `pages/` auto-discovery)
- **OAuth callback**: Handled in `app.py` before `st.navigation()`, not as a separate page

## Environment Variables

Copy `.env.example` to `.env` and set: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

## Task Management

When working with `TASK.md`, update status: ⏳ → 🚧 → ✅
