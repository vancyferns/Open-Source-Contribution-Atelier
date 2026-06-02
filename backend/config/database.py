import os
from pathlib import Path
from typing import Callable, Dict, Optional
from urllib.parse import parse_qs, unquote, urlparse


DatabaseSettings = Dict[str, Dict[str, object]]


def _read_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _has_local_postgres_env() -> bool:
    return any(_read_env(name) for name in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"))


def _build_sqlite_settings(base_dir: Path) -> DatabaseSettings:
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": base_dir / "db.sqlite3",
        }
    }


def _build_postgres_settings(database_url: str) -> Dict[str, object]:
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)
    options: Dict[str, object] = {}

    sslmode = query.get("sslmode", [""])[-1].strip()
    if sslmode:
        options["sslmode"] = sslmode

    connect_timeout = query.get("connect_timeout", [""])[-1].strip()
    if connect_timeout:
        try:
            options["connect_timeout"] = int(connect_timeout)
        except ValueError:
            pass

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/") or "postgres",
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or "",
        "CONN_MAX_AGE": int(_read_env("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": options,
    }


def _build_legacy_postgres_settings() -> Dict[str, object]:
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _read_env("DB_NAME", "contribution_atelier"),
        "USER": _read_env("DB_USER", "contribution_atelier"),
        "PASSWORD": _read_env("DB_PASSWORD", "contribution_atelier"),
        "HOST": _read_env("DB_HOST", "db"),
        "PORT": _read_env("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(_read_env("DB_CONN_MAX_AGE", "60")),
    }


def _can_connect(database_url: str) -> bool:
    try:
        import psycopg

        connection = psycopg.connect(database_url, connect_timeout=2)
    except Exception:
        return False

    connection.close()
    return True


def build_database_settings(
    base_dir: Path,
    connection_checker: Optional[Callable[[str], bool]] = None,
) -> DatabaseSettings:
    checker = connection_checker or _can_connect

    for database_url in (
        _read_env("SUPABASE_DATABASE_URL"),
        _read_env("NEON_DATABASE_URL"),
    ):
        if database_url and checker(database_url):
            return {"default": _build_postgres_settings(database_url)}

    if _has_local_postgres_env():
        legacy = _build_legacy_postgres_settings()
        # Build a DSN from legacy settings to test connectivity.
        host = legacy.get("HOST") or ""
        port = legacy.get("PORT") or "5432"
        name = legacy.get("NAME") or "contribution_atelier"
        user = legacy.get("USER") or "contribution_atelier"
        password = legacy.get("PASSWORD") or ""
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        if checker(database_url):
            return {"default": legacy}

    return _build_sqlite_settings(base_dir)

