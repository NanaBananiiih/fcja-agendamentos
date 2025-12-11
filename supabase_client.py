# supabase_client.py
import os
from supabase import create_client, Client
from typing import Optional

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # opcional (service_role)

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    # Não levantamos agora: permitirá import em ambiente sem variáveis (mas avisamos).
    raise RuntimeError(
        "Variáveis SUPABASE_URL / SUPABASE_ANON_KEY não definidas. "
        "Defina-as (Render / .env) antes de iniciar."
    )

# cliente público (anon)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def create_admin_client() -> Optional[Client]:
    """
    Retorna um cliente com service_role (privilegiado) se SUPABASE_SERVICE_ROLE_KEY
    estiver definido. Use *apenas* no backend/admin (não em apps distribuídos).
    """
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or SUPABASE_SERVICE_ROLE_KEY
    if not key:
        return None
    try:
        return create_client(SUPABASE_URL, key)
    except Exception:
        return None


def health_check() -> bool:
    """Retorna True se a tabela health responder (usado para ping/teste)."""
    try:
        resp = supabase.table("health").select("id").limit(1).execute()
        return bool(resp.data)
    except Exception:
        return False
