# app/database.py
import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Cargar variables desde .env (ubicado en la raíz del repo)
load_dotenv()

# Variables con valores por defecto seguros para local
DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
SERVER = os.getenv("DB_SERVER", "localhost\\SQLEXPRESS")
DBNAME = os.getenv("DB_NAME", "LookMyStyle")
TRUSTED = os.getenv("DB_TRUSTED", "yes").lower()  # "yes" (Windows Auth) o "no" (SQL Auth)
USER = os.getenv("DB_USER")
PWD  = os.getenv("DB_PASSWORD")

# Construir la cadena ODBC
parts = [
    f"Driver={{{DRIVER}}}",
    f"Server={SERVER}",
    f"Database={DBNAME}",
    "TrustServerCertificate=yes",
]

if TRUSTED == "yes":
    parts.append("Trusted_Connection=yes")
else:
    if not USER or not PWD:
        raise RuntimeError("DB_TRUSTED=no pero faltan DB_USER y/o DB_PASSWORD")
    parts.append(f"UID={USER}")
    parts.append(f"PWD={PWD}")

odbc_str = ";".join(parts) + ";"
DATABASE_URL = "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_str)

# --- Estas tres deben quedar definidas a nivel de módulo ---
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
