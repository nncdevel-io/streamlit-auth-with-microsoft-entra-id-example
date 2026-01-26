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

```text
src/entra_id_auth_example/
├── config.py     # AuthConfig, env loading
├── client.py     # EntraAuthClient (MSAL wrapper)
├── handlers.py   # login, logout, handle_callback, require_auth
├── app.py        # Main application
└── pages/        # Multi-page app pages
```

## Environment Variables

Copy `.env.example` to `.env` and set: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

## Task Management

When working with `TASK.md`, update status: ⏳ → 🚧 → ✅
