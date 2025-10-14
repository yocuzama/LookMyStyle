# LookMyStyle API

API en FastAPI + SQL Server (pyodbc) con autenticación JWT, CORS, Alembic y SQLAlchemy.  
IDs en UUID y columnas de autoría en todas las entidades.

## Requisitos
- Python 3.11+ recomendado
- SQL Server (LocalDB o instancia)
- ODBC Driver 17 o 18 para SQL Server

## Instalación
```bash
git clone <URL-DEL-REPO>
cd LookMyStyle
python -m venv .venv
# PowerShell:
.\.venv\Scripts\Activate.ps1
# Git Bash:
source .venv/Scripts/activate
pip install -r requirements.txt
