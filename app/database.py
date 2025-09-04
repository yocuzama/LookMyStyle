import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DRIVER   = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
SERVER   = os.getenv("DB_SERVER", r"(localdb)\MSSQLLocalDB")
DBNAME   = os.getenv("DB_NAME", "LookMyStyle")
TRUSTED  = os.getenv("DB_TRUSTED", "yes").lower()  # "yes" o "no"
USER     = os.getenv("DB_USER")
PWD      = os.getenv("DB_PASSWORD")
ENC      = os.getenv("DB_ENCRYPT", "yes").lower()
TRUST_SC = os.getenv("DB_TRUST_SERVER_CERT", "yes").lower()
TIMEOUT  = os.getenv("DB_TIMEOUT", "30")

parts = [
    f"DRIVER={{{DRIVER}}}".format(DRIVER=DRIVER),
    f"SERVER={SERVER}",
    f"DATABASE={DBNAME}",
    f"Encrypt={'yes' if ENC == 'yes' else 'no'}",
    f"TrustServerCertificate={'yes' if TRUST_SC == 'yes' else 'no'}",
    f"Connection Timeout={TIMEOUT}",
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

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass
