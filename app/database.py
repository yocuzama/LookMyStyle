"""Conexión SQLAlchemy a MSSQL mediante pyodbc y variables de entorno."""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(find_dotenv(filename=".env", usecwd=True), override=True)

DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
DB_SERVER = os.getenv("DB_SERVER", r"(localdb)\MSSQLLocalDB")
DB_NAME = os.getenv("DB_NAME", "LookMyStyle")
DB_TRUSTED = os.getenv("DB_TRUSTED", "yes")

odbc_parts = [
    f"DRIVER={{{DB_DRIVER}}}",
    f"SERVER={DB_SERVER}",
    f"DATABASE={DB_NAME}",
    "Trusted_Connection=yes" if DB_TRUSTED.lower() in {"yes", "true", "1"} else "Trusted_Connection=no",
]

if "18" in (DB_DRIVER or ""):
    odbc_parts += ["Encrypt=no", "TrustServerCertificate=yes"]

odbc_str = ";".join(odbc_parts)
odbc_url = "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_str)

print("[DB] ODBC STR =>", odbc_str)
print("[DB] URL      =>", odbc_url)

engine = create_engine(odbc_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
