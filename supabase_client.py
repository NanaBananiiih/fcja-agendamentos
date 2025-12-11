# supabase_client.py
import os
from supabase import create_client, Client
from typing import Optional

# ----------------------------------------------------------------------
# 🔐 Carrega credenciais de ambiente
# ----------------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # opcional

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError(
        "Variáveis SUPABASE_URL e SUPABASE_ANON_KEY não foram definidas.\n"
        "→ Configure-as nas variáveis de ambiente do Render ou no .env."
    )

# ----------------------------------------------------------------------
# 🌐 Cliente padrão (Anon) — usado pelo site e pelo app desktop
# ----------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# ----------------------------------------------------------------------
# 🛡️ Cliente admin (service_role) — usar somente no backend seguro
# ----------------------------------------------------------------------
def create_admin_client() -> Optional[Client]:
    """
    Cria cliente com Service Role (somente backend — NUNCA no app desktop).
    Retorna None se a chave não estiver definida.
    """
    if not SUPABASE_SERVICE_ROLE_KEY:
        return None

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


# ----------------------------------------------------------------------
# ❤️ Health check — usado para o ping semanal do GitHub Actions
# ----------------------------------------------------------------------
def health_check() -> bool:
    """
    Retorna True se a tabela 'health' responder no Supabase.
    Usado para manter o projeto ativo (anti-suspensão).
    """
    try:
        resp = supabase.table("health").select("id").limit(1).execute()
        return bool(resp.data)
    except Exception as e:
        print("Health check erro:", e)
        return False
