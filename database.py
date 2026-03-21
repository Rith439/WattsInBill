# database.py — WattsInBill MySQL Database Layer
# Requires: pip install mysql-connector-python python-dotenv
#
# Setup steps:
#   1. Start XAMPP → click Start on MySQL
#   2. Fill in your credentials in .env (DB_PASSWORD is blank by default in XAMPP)
#   3. Run `python database.py` once to verify everything works
#   4. After that, init_db() in app.py handles it on every startup
#
# Tables:
#   users                 — credentials (SHA-256 hashed passwords)
#   simulation_history    — every simulation run, linked to a user
#   simulation_appliances — per-appliance breakdown for each run
#   appliance_profiles    — saved named appliance lists per user
#   profile_appliances    — appliances inside each saved profile
#   energy_monthly        — uci_monthly data seeded from CSV
#   appliance_power       — appliance wattage reference from CSV
#   tariff_slabs          — billing slab rates

import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # reads .env from project root


# ─────────────────────────────────────────────────────────────
# CONFIG  —  all values come from .env
# ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host"    : os.getenv("DB_HOST",     "localhost"),
    "port"    : int(os.getenv("DB_PORT", "3306")),
    "user"    : os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "wattsinbill"),
}

UCI_CSV_PATH       = "data/processed/uci_monthly.csv"
APPLIANCE_CSV_PATH = "data/processed/appliance_power.csv"

BILLING_SLABS = [
    ("0–100 units",   0,   100, 3.0),
    ("101–200 units", 100, 200, 5.0),
    ("201–300 units", 200, 300, 7.0),
    ("300+ units",    300, None, 9.0),
]


# ─────────────────────────────────────────────────────────────
# CONNECTION HELPER
# ─────────────────────────────────────────────────────────────
def _get_raw_conn(include_db: bool = True):
    """Returns a raw MySQL connection. include_db=False skips database selection."""
    cfg = DB_CONFIG.copy()
    if not include_db:
        cfg.pop("database", None)
    return mysql.connector.connect(**cfg)


@contextmanager
def get_conn():
    """
    Context manager for MySQL connections.
    Auto-commits on success, rolls back on error, always closes.
    """
    conn = _get_raw_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# DATABASE + TABLE CREATION
# ─────────────────────────────────────────────────────────────
def _create_database_if_missing():
    """
    Creates the database itself if it doesn't exist yet.
    Connects without a database so it works on a brand new MySQL install.
    """
    conn = _get_raw_conn(include_db=False)
    cur  = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    cur.close()
    conn.close()


# Each string is one CREATE TABLE statement
SCHEMA_STATEMENTS = [

    """CREATE TABLE IF NOT EXISTS users (
        id            INT         NOT NULL AUTO_INCREMENT,
        username      VARCHAR(80) NOT NULL UNIQUE,
        password_hash CHAR(64)    NOT NULL,
        created_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS simulation_history (
        id                INT         NOT NULL AUTO_INCREMENT,
        user_id           INT         NOT NULL,
        run_at            DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        days              TINYINT     NOT NULL,
        ml_predicted_kwh  DOUBLE      NOT NULL,
        appliance_kwh     DOUBLE      NOT NULL,
        adjustment_factor DOUBLE      NOT NULL,
        deviation_pct     DOUBLE      NOT NULL,
        usage_flag        VARCHAR(20) NOT NULL,
        final_kwh         DOUBLE      NOT NULL,
        energy_charge     DOUBLE      NOT NULL,
        fixed_charge      DOUBLE      NOT NULL,
        meter_rent        DOUBLE      NOT NULL,
        total_bill        DOUBLE      NOT NULL,
        slab_alert        TEXT,
        PRIMARY KEY (id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS simulation_appliances (
        id             INT         NOT NULL AUTO_INCREMENT,
        simulation_id  INT         NOT NULL,
        appliance      VARCHAR(60) NOT NULL,
        power_kw       DOUBLE      NOT NULL,
        hours_day      DOUBLE      NOT NULL,
        quantity       TINYINT     NOT NULL,
        monthly_kwh    DOUBLE      NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (simulation_id) REFERENCES simulation_history(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS appliance_profiles (
        id         INT         NOT NULL AUTO_INCREMENT,
        user_id    INT         NOT NULL,
        name       VARCHAR(80) NOT NULL,
        created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uq_user_profile (user_id, name),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS profile_appliances (
        id         INT         NOT NULL AUTO_INCREMENT,
        profile_id INT         NOT NULL,
        appliance  VARCHAR(60) NOT NULL,
        hours_day  DOUBLE      NOT NULL,
        quantity   TINYINT     NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (profile_id) REFERENCES appliance_profiles(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS energy_monthly (
        id         INT         NOT NULL AUTO_INCREMENT,
        month      VARCHAR(10) NOT NULL UNIQUE,
        energy_kwh DOUBLE      NOT NULL,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS appliance_power (
        id        INT         NOT NULL AUTO_INCREMENT,
        appliance VARCHAR(60) NOT NULL UNIQUE,
        power_kw  DOUBLE      NOT NULL,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

    """CREATE TABLE IF NOT EXISTS tariff_slabs (
        id           INT         NOT NULL AUTO_INCREMENT,
        label        VARCHAR(40) NOT NULL,
        units_from   INT         NOT NULL,
        units_to     INT,
        rate_per_kwh DOUBLE      NOT NULL,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
]


def _create_tables():
    with get_conn() as conn:
        cur = conn.cursor()
        for stmt in SCHEMA_STATEMENTS:
            cur.execute(stmt)
        cur.close()


# ─────────────────────────────────────────────────────────────
# SEEDING  —  runs only once (checks row count first)
# ─────────────────────────────────────────────────────────────
def _seed_energy_data():
    if not Path(UCI_CSV_PATH).exists():
        return
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM energy_monthly")
        if cur.fetchone()[0] > 0:
            cur.close(); return
        df   = pd.read_csv(UCI_CSV_PATH)
        rows = [(str(r["month"]), float(r["energy_kwh"])) for _, r in df.iterrows()]
        cur.executemany(
            "INSERT IGNORE INTO energy_monthly (month, energy_kwh) VALUES (%s, %s)", rows
        )
        cur.close()


def _seed_appliance_data():
    if not Path(APPLIANCE_CSV_PATH).exists():
        return
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM appliance_power")
        if cur.fetchone()[0] > 0:
            cur.close(); return
        df   = pd.read_csv(APPLIANCE_CSV_PATH)
        rows = [(str(r["appliance"]).lower(), float(r["power_kw"])) for _, r in df.iterrows()]
        cur.executemany(
            "INSERT IGNORE INTO appliance_power (appliance, power_kw) VALUES (%s, %s)", rows
        )
        cur.close()


def _seed_tariff_slabs():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tariff_slabs")
        if cur.fetchone()[0] > 0:
            cur.close(); return
        cur.executemany(
            "INSERT INTO tariff_slabs (label, units_from, units_to, rate_per_kwh) VALUES (%s,%s,%s,%s)",
            BILLING_SLABS
        )
        cur.close()


def init_db():
    """
    Full initialization — safe to call on every app startup.
      1. Creates the MySQL database if it doesn't exist
      2. Creates all 8 tables  (IF NOT EXISTS — never wipes existing data)
      3. Seeds reference tables from CSVs (only on very first run)
    """
    _create_database_if_missing()
    _create_tables()
    _seed_energy_data()
    _seed_appliance_data()
    _seed_tariff_slabs()


# ─────────────────────────────────────────────────────────────
# AUTH — USERS
# ─────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username: str, password: str) -> tuple[bool, str]:
    """Registers a new user. Returns (success, message)."""
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, _hash(password))
            )
            cur.close()
        return True, "Account created successfully!"
    except mysql.connector.IntegrityError:
        return False, "Username already taken."


def login_user(username: str, password: str) -> tuple[bool, str, int | None]:
    """Validates credentials. Returns (success, message, user_id)."""
    username = username.strip().lower()
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, password_hash FROM users WHERE username = %s", (username,)
        )
        row = cur.fetchone()
        cur.close()
    if not row:
        return False, "Invalid username or password.", None
    if row["password_hash"] != _hash(password):
        return False, "Invalid username or password.", None
    return True, "Login successful.", row["id"]


def get_user_id(username: str) -> int | None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username.strip().lower(),))
        row = cur.fetchone()
        cur.close()
    return row[0] if row else None


# ─────────────────────────────────────────────────────────────
# SIMULATION HISTORY
# ─────────────────────────────────────────────────────────────
def save_simulation(user_id: int, result: dict, days: int) -> int:
    """Saves a full simulation result. Returns new simulation_id."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO simulation_history
               (user_id, days, ml_predicted_kwh, appliance_kwh, adjustment_factor,
                deviation_pct, usage_flag, final_kwh, energy_charge, fixed_charge,
                meter_rent, total_bill, slab_alert)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                user_id, days,
                result["ml_predicted_kwh"], result["appliance_kwh"],
                result["adjustment_factor"], result["deviation_pct"],
                result["usage_flag"],        result["final_kwh"],
                result["energy_charge"],     result["fixed_charge"],
                result["meter_rent"],        result["total_bill"],
                result.get("slab_alert", ""),
            )
        )
        sim_id = cur.lastrowid
        for item in result.get("appliance_breakdown", []):
            cur.execute(
                """INSERT INTO simulation_appliances
                   (simulation_id, appliance, power_kw, hours_day, quantity, monthly_kwh)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (sim_id, item["appliance"], item["power_kw"],
                 item["hours_day"], item["quantity"], item["monthly_kwh"])
            )
        cur.close()
    return sim_id


def get_simulation_history(user_id: int, limit: int = 20) -> list[dict]:
    """Returns the last `limit` runs for a user, newest first."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM simulation_history WHERE user_id = %s ORDER BY run_at DESC LIMIT %s",
            (user_id, limit)
        )
        rows = cur.fetchall()
        for row in rows:
            cur.execute(
                "SELECT * FROM simulation_appliances WHERE simulation_id = %s", (row["id"],)
            )
            row["appliances"] = cur.fetchall()
        cur.close()
    return rows


def delete_simulation(sim_id: int, user_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM simulation_history WHERE id = %s AND user_id = %s", (sim_id, user_id)
        )
        deleted = cur.rowcount > 0
        cur.close()
    return deleted


def get_simulation_stats(user_id: int) -> dict:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT COUNT(*) AS total_runs, AVG(total_bill) AS avg_bill,
                      MIN(total_bill) AS min_bill, MAX(total_bill) AS max_bill,
                      AVG(final_kwh)  AS avg_kwh
               FROM simulation_history WHERE user_id = %s""",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
    return row if row else {}


# ─────────────────────────────────────────────────────────────
# APPLIANCE PROFILES
# ─────────────────────────────────────────────────────────────
def save_appliance_profile(user_id: int, name: str, appliances: list) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Profile name cannot be empty."
    if not appliances:
        return False, "Add at least one appliance before saving."
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO appliance_profiles (user_id, name) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE name = VALUES(name)",
                (user_id, name)
            )
            cur.execute(
                "SELECT id FROM appliance_profiles WHERE user_id = %s AND name = %s",
                (user_id, name)
            )
            profile_id = cur.fetchone()[0]
            cur.execute("DELETE FROM profile_appliances WHERE profile_id = %s", (profile_id,))
            for item in appliances:
                cur.execute(
                    "INSERT INTO profile_appliances (profile_id, appliance, hours_day, quantity) "
                    "VALUES (%s,%s,%s,%s)",
                    (profile_id, item["name"], item["hours"], item["quantity"])
                )
            cur.close()
        return True, f'Profile "{name}" saved!'
    except mysql.connector.IntegrityError:
        return False, "A profile with that name already exists."


def get_appliance_profiles(user_id: int) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM appliance_profiles WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        profiles = cur.fetchall()
        for p in profiles:
            cur.execute(
                "SELECT * FROM profile_appliances WHERE profile_id = %s", (p["id"],)
            )
            p["appliances"] = [
                {"name": a["appliance"], "hours": a["hours_day"], "quantity": a["quantity"]}
                for a in cur.fetchall()
            ]
        cur.close()
    return profiles


def delete_appliance_profile(profile_id: int, user_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM appliance_profiles WHERE id = %s AND user_id = %s",
            (profile_id, user_id)
        )
        deleted = cur.rowcount > 0
        cur.close()
    return deleted


# ─────────────────────────────────────────────────────────────
# REFERENCE DATA QUERIES
# ─────────────────────────────────────────────────────────────
def get_energy_monthly() -> pd.DataFrame:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT month, energy_kwh FROM energy_monthly ORDER BY month")
        rows = cur.fetchall()
        cur.close()
    return pd.DataFrame(rows)


def get_appliance_power() -> dict:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT appliance, power_kw FROM appliance_power")
        rows = cur.fetchall()
        cur.close()
    return {r[0]: r[1] for r in rows}


def get_tariff_slabs() -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM tariff_slabs ORDER BY units_from")
        rows = cur.fetchall()
        cur.close()
    return rows


# ─────────────────────────────────────────────────────────────
# MAIN — run directly to initialize and verify
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Initializing WattsInBill MySQL database...")
    init_db()
    print(f"✅ Connected to MySQL → database: `{DB_CONFIG['database']}`\n")

    with get_conn() as conn:
        cur = conn.cursor()
        tables = [
            "users", "simulation_history", "simulation_appliances",
            "appliance_profiles", "profile_appliances",
            "energy_monthly", "appliance_power", "tariff_slabs"
        ]
        print(f"Tables created ({len(tables)}):")
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t:<28} {cur.fetchone()[0]:>5} rows")
        cur.close()