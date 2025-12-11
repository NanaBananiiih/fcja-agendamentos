# supabase_client.py
import os
from supabase import create_client, Client
from typing import Optional

# Carrega variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # opcional


def _warn_missing_env():
    """Avisa no console caso as variáveis não estejam definidas."""
    print(
        "\n[AVISO] Variáveis SUPABASE_URL e/ou SUPABASE_ANON_KEY não estão definidas.\n"
        "O cliente Supabase será 'None' e funções que dependam dele irão falhar.\n"
        "Defina no .env ou no painel do Render.\n"
    )


# ---------------------------------------------------------
# Cliente público (anon)
# ---------------------------------------------------------
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print("[ERRO] Falha ao criar cliente Supabase:", e)
        supabase = None
else:
    _warn_missing_env()


# ---------------------------------------------------------
# Cliente administrativo (service_role)
# ---------------------------------------------------------
def create_admin_client() -> Optional[Client]:
    """
    Retorna um cliente com service_role (privilegiado)
    somente se SUPABASE_SERVICE_ROLE_KEY estiver definido.
    NÃO use service_role no frontend!
    """
    key = SUPABASE_SERVICE_ROLE_KEY
    if not key:
        return None

    if not SUPABASE_URL:
        return None

    try:
        return create_client(SUPABASE_URL, key)
    except Exception:
        return None


# ---------------------------------------------------------
# Health Check opcional
# ---------------------------------------------------------
def health_check() -> bool:
    """
    Tenta consultar a tabela 'health'. Apenas para testes.
    Retorna False se não for possível.
    """
    if not supabase:
        return False

    try:
        resp = supabase.table("health").select("id").limit(1).execute()
        return bool(resp.data)
    except Exception:
        return False
