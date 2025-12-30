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

    load_dotenv(override=False)

_load_env_robusto()

# -------------------------
# Import supabase client
# -------------------------
try:
    from supabase_client import supabase, create_admin_client  # type: ignore
except Exception as e:
    print("[database.py] Aviso: falha ao importar supabase_client:", e)
    supabase = None  # type: ignore
    def create_admin_client():
        return None

# -------------------------
# Helpers
# -------------------------
def _safe_resp_data(resp) -> Optional[Any]:
    if resp is None:
        return None
    return getattr(resp, "data", None)

def _supabase_ok() -> bool:
    return (supabase is not None)

# -------------------------
# INSERÇÕES
# -------------------------
def insert_visitante(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not _supabase_ok():
        return None

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
        return None

    payload = {
        "nome_ies": data.get("nome_ies") or "",
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
        resp = supabase.table("ies").insert(payload).execute()
        d = _safe_resp_data(resp)
        return d[0] if d else None
    except Exception as e:
        print("Erro insert_ies:", e)
        return None

def insert_pesquisador(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not _supabase_ok():
        return None

    payload = {
        "nome": data.get("nome") or "",
        "genero": data.get("genero") or "",
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
# LOGIN (CORRIGIDO – SERVICE ROLE)
# -------------------------
def get_usuario(username: str, password: str) -> Optional[Dict[str, Any]]:
    admin = create_admin_client()
    if not admin:
        print("get_usuario: admin client indisponível.")
        return None

    try:
        resp = (
            admin.table("usuarios")
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

# -------------------------
# HEALTH CHECK
# -------------------------
def health_check() -> bool:
    if not _supabase_ok():
        return False
    try:
        resp = supabase.table("health").select("id").limit(1).execute()
        return _safe_resp_data(resp) is not None
    except Exception:
        return False