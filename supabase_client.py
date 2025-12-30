# supabase_client.py
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

# -------------------------------------------------
# Carregar .env da RAIZ do projeto
# (funciona em Python normal e em .exe do PyInstaller)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# se estiver rodando como .exe (PyInstaller)
if hasattr(os, "_MEIPASS"):
    ENV_PATH = Path(os._MEIPASS) / ".env"
else:
    ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # opcional


def _warn_missing_env():
    print(
        "\n[AVISO] Variáveis SUPABASE_URL e/ou SUPABASE_ANON_KEY não estão definidas.\n"
        "O cliente Supabase será 'None' e funções que dependam dele irão falhar.\n"
        "Defina no .env da raiz do projeto ou inclua no PyInstaller.\n"
    )


# -------------------------------------------------
# Cliente público (anon) → usado no app normal
# -------------------------------------------------
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print("[ERRO] Falha ao criar cliente Supabase:", e)
        supabase = None
else:
    _warn_missing_env()


# -------------------------------------------------
# Cliente administrativo (service_role) → SOMENTE LOGIN
# -------------------------------------------------
def create_admin_client() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        return None


# -------------------------------------------------
# Health Check opcional (ping)
# -------------------------------------------------
def health_check() -> bool:
    if not supabase:
        return False
    try:
        resp = supabase.table("health").select("id").limit(1).execute()
        return bool(resp.data)
    except Exception:
        return False