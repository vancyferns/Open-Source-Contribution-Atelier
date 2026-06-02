from __future__ import annotations

from pathlib import Path
from typing import List

from config.database import build_database_settings


def test_prefers_supabase_when_available(monkeypatch):
    monkeypatch.setenv("SUPABASE_DATABASE_URL", "postgresql://supabase_user:supabase_pass@supabase.example.com:5432/supabase_db")
    monkeypatch.setenv("NEON_DATABASE_URL", "postgresql://neon_user:neon_pass@neon.example.com:5432/neon_db")

    calls: List[str] = []

    def connection_checker(database_url: str) -> bool:
        calls.append(database_url)
        return "supabase" in database_url

    databases = build_database_settings(Path("C:/tmp"), connection_checker=connection_checker)

    assert databases["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert databases["default"]["NAME"] == "supabase_db"
    assert calls == [
        "postgresql://supabase_user:supabase_pass@supabase.example.com:5432/supabase_db",
    ]


def test_falls_back_to_neon_when_supabase_is_unreachable(monkeypatch):
    monkeypatch.setenv("SUPABASE_DATABASE_URL", "postgresql://supabase_user:supabase_pass@supabase.example.com:5432/supabase_db")
    monkeypatch.setenv("NEON_DATABASE_URL", "postgresql://neon_user:neon_pass@neon.example.com:5432/neon_db")

    calls: List[str] = []

    def connection_checker(database_url: str) -> bool:
        calls.append(database_url)
        return "neon" in database_url

    databases = build_database_settings(Path("C:/tmp"), connection_checker=connection_checker)

    assert databases["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert databases["default"]["NAME"] == "neon_db"
    assert calls == [
        "postgresql://supabase_user:supabase_pass@supabase.example.com:5432/supabase_db",
        "postgresql://neon_user:neon_pass@neon.example.com:5432/neon_db",
    ]


def test_falls_back_to_sqlite_when_legacy_postgres_is_unreachable(monkeypatch):
    monkeypatch.delenv("SUPABASE_DATABASE_URL", raising=False)
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_NAME", "atelier_db")
    monkeypatch.setenv("DB_USER", "atelier_user")
    monkeypatch.setenv("DB_PASSWORD", "atelier_pass")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")

    databases = build_database_settings(Path("C:/tmp"), connection_checker=lambda _: False)

    assert databases["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert str(databases["default"]["NAME"]).endswith("db.sqlite3")


def test_defaults_to_sqlite_when_no_database_envs_are_set(monkeypatch):
    monkeypatch.delenv("SUPABASE_DATABASE_URL", raising=False)
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)

    databases = build_database_settings(Path("C:/tmp"), connection_checker=lambda _: False)

    assert databases["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert str(databases["default"]["NAME"]).endswith("db.sqlite3")