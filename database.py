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
    Procura .env nos diretórios mais comuns.
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

    load_dotenv(override=False)


_load_env_robusto()

# -------------------------
# Variáveis necessárias (somente estas)
# -------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Verificação simples
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError(
        "Erro: SUPABASE_URL e SUPABASE_ANON_KEY precisam estar definidos no .env ou nas variáveis do Render."
    )

# -------------------------
# Importa cliente do Supabase
# -------------------------
from supabase_client import supabase  # type: ignore


def insert_visitante(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("visitante").insert(data).execute()
        return resp.data[0] if getattr(resp, "data", None) else None
    except Exception as e:
        print("Erro insert_visitante:", e)
        return None


def insert_escola(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("escola").insert(data).execute()
        return resp.data[0] if getattr(resp, "data", None) else None
    except Exception as e:
        print("Erro insert_escola:", e)
        return None


def insert_ies(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("ies").insert(data).execute()
        return resp.data[0] if getattr(resp, "data", None) else None
    except Exception as e:
        print("Erro insert_ies:", e)
        return None


def insert_pesquisador(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("pesquisador").insert(data).execute()
        return resp.data[0] if getattr(resp, "data", None) else None
    except Exception as e:
        print("Erro insert_pesquisador:", e)
        return None


def get_usuario(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Retorna o usuário (login interno).
    """
    try:
        resp = (
            supabase.table("usuarios")
            .select("*")
            .eq("username", username)
            .eq("password", password)
            .limit(1)
            .execute()
        )
        return resp.data[0] if getattr(resp, "data", None) else None
    except Exception as e:
        print("Erro get_usuario:", e)
        return None


def list_visitantes(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        resp = supabase.table("visitante").select("*").order("id", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print("Erro list_visitantes:", e)
        return []


def list_escolas(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        resp = supabase.table("escola").select("*").order("id", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print("Erro list_escolas:", e)
        return []


def list_ies(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        resp = supabase.table("ies").select("*").order("id", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print("Erro list_ies:", e)
        return []


def list_pesquisadores(limit: int = 100) -> List[Dict[str, Any]]:
    try:
        resp = supabase.table("pesquisador").select("*").order("id", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print("Erro list_pesquisadores:", e)
        return []