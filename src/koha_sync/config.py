from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv


def _load_environment() -> None:
    """Load environment variables from a .env file if present."""
    cwd_env = Path.cwd() / ".env"
    project_env = Path(__file__).resolve().parents[2] / ".env"

    # Load cwd .env first, then project level to allow overrides.
    if cwd_env.exists():
        load_dotenv(cwd_env)
    if project_env.exists() and project_env != cwd_env:
        load_dotenv(project_env)
    else:
        # Fallback to default search
        load_dotenv()


@dataclass(slots=True)
class Settings:
    db_connection_string: str | None = None
    db_dsn: str | None = None
    db_username: str | None = None
    db_password: str | None = None

    students_query: str = (
        "SELECT reg_no, first_name, surname, email, phone, course, level FROM vw_students WHERE active = 1"
    )
    active_where_clause: str = ""

    koha_branch: str = "MAIN"
    koha_category: str = "STUD"
    koha_static_attributes: Dict[str, str] = field(default_factory=dict)

    host: str = "0.0.0.0"
    port: int = 8100

    def connection_string(self) -> str:
        """Derive a pyodbc connection string from the supplied settings."""
        if self.db_connection_string:
            return self.db_connection_string

        if not self.db_dsn:
            raise ValueError(
                "Either DB_CONNECTION_STRING or DB_DSN must be provided for the database connection."
            )

        credentials = []
        if self.db_username:
            credentials.append(f"UID={self.db_username}")
        if self.db_password:
            credentials.append(f"PWD={self.db_password}")

        credential_part = ";".join(credentials)
        if credential_part:
            credential_part = ";" + credential_part

        return f"DSN={self.db_dsn}{credential_part};"


def _parse_static_attributes(raw: str | None) -> Dict[str, str]:
    if not raw:
        return {}

    attributes: Dict[str, str] = {}
    for item in raw.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(
                f"Unable to parse KOHA_STATIC_ATTRIBUTES entry '{item}'. Expected format type=value."
            )
        key, value = item.split("=", 1)
        attributes[key.strip()] = value.strip()
    return attributes


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings loaded from environment."""
    _load_environment()

    static_attrs = _parse_static_attributes(os.getenv("KOHA_STATIC_ATTRIBUTES"))

    settings = Settings(
        db_connection_string=os.getenv("DB_CONNECTION_STRING"),
        db_dsn=os.getenv("DB_DSN"),
        db_username=os.getenv("DB_USERNAME"),
        db_password=os.getenv("DB_PASSWORD"),
        students_query=os.getenv("STUDENTS_QUERY")
        or Settings.students_query,
        active_where_clause=os.getenv("ACTIVE_WHERE_CLAUSE", "").strip(),
        koha_branch=os.getenv("KOHA_BRANCH", Settings.koha_branch),
        koha_category=os.getenv("KOHA_CATEGORY", Settings.koha_category),
        koha_static_attributes=static_attrs,
        host=os.getenv("HOST", Settings.host),
        port=int(os.getenv("PORT", Settings.port)),
    )

    return settings
