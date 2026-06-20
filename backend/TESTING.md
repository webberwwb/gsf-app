# Order pricing tests

Run all automated tests (SQLite in-memory — **never prod MySQL**):

```bash
cd backend && python run_tests.py
```

## Rules

- **Do not** call `create_app()` with default `Config` in tests.
- Use `TestConfig` (`sqlite:///:memory:`) via `tests/conftest.py` fixtures.
- Pure unit tests (points, shipping tier math) need no database.
- DB integration tests live in `tests/` and use pytest fixtures only.

## Manual prod investigation (read-only)

Audit mismatched order headers vs line sums:

```bash
cd backend && python scripts/audit_order_total_mismatches.py
```

This connects to whatever `MYSQL_*` env is set (often prod on localhost). **Read-only** — no fixes.

## Optional file SQLite (debug)

Set `GSF_TEST_SQLITE_FILE=1` to use a file under `backend/.test-data/` (gitignored) — not implemented by default; in-memory is preferred.
