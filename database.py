# database.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

# -------------------------
# Carregamento de .env robusto
# -------------------------
def _load_env_robusto() -> None:
    """
    Procura .env nos diretórios mais comuns e carrega o primeiro encontrado.
    """
    exe_dir = Path(getattr(sys, "_MEIPASS", Path(sys.argv[0]).resolve().parent))
    cwd = Path.cwd()
    here = Path(__file__).resolve().parent
    project_root = here.parent if (here.name.lower() == "desktop") else here

    candidatos = [
        exe_dir / ".env",
        cwd / ".env",
        here / ".env",
        project_root / ".env",
    ]

    for p in candidatos:
        if p.exists():
            load_dotenv(dotenv_path=p, override=False)
            return

    # fallback padrão (pode ler do CWD)
    load_dotenv(override=False)


_load_env_robusto()

# -------------------------
# Variáveis de ambiente (somente leitura)
# -------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # opcional

# -------------------------
# Import supabase client (import seguro)
# -------------------------
try:
    # supabase_client.py deve criar 'supabase' via create_client(...)
    from supabase_client import supabase, create_admin_client  # type: ignore
except Exception as e:
    # não quebrar o import do módulo — só avisar
    print("[database.py] Aviso: não foi possível importar supabase_client:", e)
    supabase = None  # type: ignore
    def create_admin_client():
        return None

# -------------------------
# Helpers
# -------------------------
def _safe_resp_data(resp) -> Optional[Any]:
    """Retorna resp.data quando disponível, else None (evita AttributeError)."""
    if resp is None:
        return None
    return getattr(resp, "data", None)

def _supabase_ok() -> bool:
    """Retorna True se o cliente supabase foi inicializado com sucesso."""
    return (supabase is not None)

# -------------------------
# Inserções (runtime via Supabase - recomendado)
# -------------------------
def insert_visitante(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insere um visitante via Supabase.
    Campos aceitos (recomendados): nome, genero, email, telefone, endereco, qtd_pessoas, data, turno, horario_chegada, duracao, observacao
    Retorna o registro inserido (dict) ou None em caso de erro.
    """
    if not _supabase_ok():
        print("insert_visitante: supabase client indisponível.")
        return None

    # normaliza valores para evitar NOT NULL violação
    payload = {
        "nome": data.get("nome") or "",
        "genero": data.get("genero") or "",
        "email": data.get("email") or "",
        "telefone": data.get("telefone") or "",
        "endereco": data.get("endereco") or "",
        "qtd_pessoas": int(data.get("qtd_pessoas") or 0),
        "data": data.get("data"),
        "turno": data.get("turno") or "",
        "horario_chegada": data.get("horario_chegada") or "",
        "duracao": data.get("duracao") or "",
        "observacao": data.get("observacao") or "",
    }

    try:
        resp = supabase.table("visitante").insert(payload).execute()
        d = _safe_resp_data(resp)
        return d[0] if d else None
    except Exception as e:
        print("Erro insert_visitante:", e)
        return None

def insert_escola(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not _supabase_ok():
        print("insert_escola: supabase client indisponível.")
        return None

    payload = {
        "nome_escola": data.get("nome_escola") or "",
        "representante": data.get("representante") or "",
        "email": data.get("email") or "",
        "telefone": data.get("telefone") or "",
        "endereco": data.get("endereco") or "",
        "num_alunos": int(data.get("num_alunos") or 0),
        "data": data.get("data"),
        "turno": data.get("turno") or "",
        "horario_chegada": data.get("horario_chegada") or "",
        "duracao": data.get("duracao") or "",
        "observacao": data.get("observacao") or "",
    }

    try:
        resp = supabase.table("escola").insert(payload).execute()
        d = _safe_resp_data(resp)
        return d[0] if d else None
    except Exception as e:
        print("Erro insert_escola:", e)
        return None

def insert_ies(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not _supabase_ok():
        print("insert_ies: supabase client indisponível.")
        return None

    # aceita 'representante' ou fallback 'responsavel' (compatibilidade)
    representante = data.get("representante") or data.get("responsavel") or ""

    payload = {
        "nome_ies": data.get("nome_ies") or "",
        "representante": representante,
        "email": data.get("email") or "",
        "telefone": data.get("telefone") or "",
        "endereco": data.get("endereco") or "",
        "num_alunos": int(data.get("num_alunos") or 0),
        "data": data.get("data"),
        "turno": data.get("turno") or "",
        "horario_chegada": data.get("horario_chegada") or "",
        "duracao": data.get("duracao") or "",
        "observacao": data.get("observacao") or "",
    }

    try:
        resp = supabase.table("ies").insert(payload).execute()
        d = _safe_resp_data(resp)
        return d[0] if d else None
    except Exception as e:
        # PostgREST pode retornar dict-like error; imprimimos legível
        print("Erro insert_ies:", e)
        return None

def insert_pesquisador(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not _supabase_ok():
        print("insert_pesquisador: supabase client indisponível.")
        return None

    # Garante que 'genero' (NOT NULL) não seja None
    genero = data.get("genero")
    genero = genero if genero is not None else ""

    payload = {
        "nome": data.get("nome") or "",
        "genero": genero,
        "email": data.get("email") or "",
        "telefone": data.get("telefone") or "",
        "instituicao": data.get("instituicao") or "",
        "pesquisa": data.get("pesquisa") or "",
        "data": data.get("data"),
        "turno": data.get("turno") or "",
        "horario_chegada": data.get("horario_chegada") or "",
        "duracao": data.get("duracao") or "",
        "observacao": data.get("observacao") or "",
    }

    try:
        resp = supabase.table("pesquisador").insert(payload).execute()
        d = _safe_resp_data(resp)
        return d[0] if d else None
    except Exception as e:
        print("Erro insert_pesquisador:", e)
        return None

# -------------------------
# Consultas / listagens
# -------------------------
def get_usuario(username: str, password: str) -> Optional[Dict[str, Any]]:
    if not _supabase_ok():
        print("get_usuario: supabase client indisponível.")
        return None
    try:
        resp = (
            supabase.table("usuarios")
            .select("*")
            .eq("username", username)
            .eq("password", password)
            .limit(1)
            .execute()
        )
        d = _safe_resp_data(resp)
        return d[0] if d else None
    except Exception as e:
        print("Erro get_usuario:", e)
        return None

def list_visitantes(limit: int = 100) -> List[Dict[str, Any]]:
    if not _supabase_ok():
        print("list_visitantes: supabase client indisponível.")
        return []
    try:
        resp = supabase.table("visitante").select("*").order("id", desc=True).limit(limit).execute()
        return _safe_resp_data(resp) or []
    except Exception as e:
        print("Erro list_visitantes:", e)
        return []

def list_escolas(limit: int = 100) -> List[Dict[str, Any]]:
    if not _supabase_ok():
        print("list_escolas: supabase client indisponível.")
        return []
    try:
        resp = supabase.table("escola").select("*").order("id", desc=True).limit(limit).execute()
        return _safe_resp_data(resp) or []
    except Exception as e:
        print("Erro list_escolas:", e)
        return []

def list_ies(limit: int = 100) -> List[Dict[str, Any]]:
    if not _supabase_ok():
        print("list_ies: supabase client indisponível.")
        return []
    try:
        resp = supabase.table("ies").select("*").order("id", desc=True).limit(limit).execute()
        return _safe_resp_data(resp) or []
    except Exception as e:
        print("Erro list_ies:", e)
        return []

def list_pesquisadores(limit: int = 100) -> List[Dict[str, Any]]:
    if not _supabase_ok():
        print("list_pesquisadores: supabase client indisponível.")
        return []
    try:
        resp = supabase.table("pesquisador").select("*").order("id", desc=True).limit(limit).execute()
        return _safe_resp_data(resp) or []
    except Exception as e:
        print("Erro list_pesquisadores:", e)
        return []

# -------------------------
# Health check utilitário
# -------------------------
def health_check() -> bool:
    """
    Testa se o supabase responder (tabela 'health' ou 'visitante').
    Retorna False se cliente indisponível ou chamada falhar.
    """
    if not _supabase_ok():
        return False
    try:
        # tenta tabela health (se criada)
        resp = supabase.table("health").select("id").limit(1).execute()
        if _safe_resp_data(resp) is not None:
            return True
    except Exception:
        pass

    try:
        resp = supabase.table("visitante").select("id").limit(1).execute()
        return _safe_resp_data(resp) is not None
    except Exception:
        return False