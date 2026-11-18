"""Transactional COPY loading; no credentials are printed or embedded in source."""

import hashlib
import json
import os

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from platform_app.config import Settings
from platform_app.generate import TABLE_COLUMNS


def connect():
    return psycopg.connect(
        host=os.getenv("PG_HOST", "127.0.0.1"),
        port=int(os.getenv("PG_PORT", "55432")),
        dbname=os.getenv("PG_DATABASE", "analytics"),
        user=os.getenv("PG_USER", "analytics"),
        password=os.getenv("PG_PASSWORD", ""),
        options="-c timezone=UTC",
        row_factory=dict_row,
    )


def query(statement, params=None) -> list[dict]:
    with connect() as conn:
        return conn.execute(statement, params).fetchall()


def load_raw(settings: Settings) -> dict:
    manifest = json.loads((settings.generated / "manifest.json").read_text())
    if (manifest["seed"], manifest["users"], manifest["start"], manifest["end"]) != (
        settings.seed,
        settings.users,
        str(settings.start),
        str(settings.end),
    ):
        raise ValueError("Generated source manifest differs from current configuration; regenerate")
    for table in TABLE_COLUMNS:
        if (
            hashlib.sha256((settings.generated / f"{table}.csv").read_bytes()).hexdigest()
            != manifest["sha256"][table]
        ):
            raise ValueError(f"Source checksum mismatch: {table}")
    with connect() as conn:
        conn.execute((settings.root / "sql" / "raw.sql").read_text())
        tables = [sql.Identifier("raw", t) for t in TABLE_COLUMNS]
        conn.execute(
            sql.SQL("TRUNCATE {}, control.ml_predictions").format(sql.SQL(", ").join(tables))
        )
        conn.execute("TRUNCATE reporting.data_quality")
        for table, columns in TABLE_COLUMNS.items():
            statement = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)").format(
                sql.Identifier("raw", table), sql.SQL(",").join(map(sql.Identifier, columns))
            )
            with conn.cursor().copy(statement) as copy:
                with (settings.generated / f"{table}.csv").open("rb") as file:
                    while chunk := file.read(1024 * 1024):
                        copy.write(chunk)
            observed = conn.execute(
                sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier("raw", table))
            ).fetchone()["n"]
            if observed != manifest["counts"][table]:
                raise ValueError(f"Row count differs for {table}")
            conn.execute(sql.SQL("ANALYZE {}").format(sql.Identifier("raw", table)))
        conn.execute(
            "INSERT INTO control.run_config VALUES(1,%s,%s,%s,now()) ON CONFLICT(singleton) DO UPDATE SET seed=excluded.seed, history_start=excluded.history_start, history_end=excluded.history_end,loaded_at=excluded.loaded_at",
            (settings.seed, settings.start, settings.end),
        )
    return manifest["counts"]
