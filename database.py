# database.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

# --- psycopg2 é opcional (só para init_db / admin operations)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None  # ok se não estiver instalado no ambiente de runtime

# --- cliente Supabase (HTTP) - veja supabase_client.py
# Espera-se que exista:
#   - supabase: cliente público (anon) para operações HTTP
#   - create_admin_client(): opcional, cria cliente service_role se SERVICE_ROLE_KEY definido
from supabase_client import supabase, create_admin_client  # type: ignore

# -------------------------
# Carregamento de .env robusto
# -------------------------
def _load_env_robusto() -> None:
    """
    Procura .env nas localizações mais comuns:
      - diretório do executável (PyInstaller)
      - diretório atual (CWD)
      - pasta deste arquivo (modo dev)
      - raiz do projeto (um nível acima de desktop/)
    Carrega o primeiro que existir. Não sobrescreve variáveis já definidas.
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
# Variáveis de ambiente
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL")  # opcional: usado apenas para admin/init
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# service role key (opcional; usar apenas em backend seguro)
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


# -------------------------
# Helper: instrução rápida para percent-encode de senha (não executa nada)
# -------------------------
# Se sua senha contém caracteres especiais (ex: "@"), use:
# from urllib.parse import quote_plus
# senha_encoded = quote_plus("SUA_SENHA_AQUI")
# DATABASE_URL = f"postgresql://usuario:{senha_encoded}@host:5432/db"
#
# NÃO coloque chaves/senhas neste arquivo. Use env vars no Render / .env local.


# -------------------------
# Funções utilitárias para conexão via psycopg2 (admin)
# -------------------------
def get_connection():
    """
    Abre conexão Postgres via psycopg2.
    Levanta RuntimeError se DATABASE_URL ausente.
    Útil apenas para init_db / operações administrativas diretas.
    """
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não encontrada. Defina DATABASE_URL para usar get_connection() / init_db()."
        )
    if not psycopg2:
        raise RuntimeError("psycopg2 não está instalado neste ambiente.")
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)


# -----------------------
# Funções que usam Supabase (recomendado para runtime)
# -----------------------
# Usam o cliente público (anon) exposto em supabase_client.supabase
# Sempre retornam dicionários / listas (ou None em caso de erro).
# -----------------------

def insert_visitante(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insere um registro na tabela visitante via Supabase (PostgREST).
    data deve conter chaves compatíveis com a tabela (ex.: nome, genero, email, telefone, endereco, qtd_pessoas, data, turno, tempo_estimado, observacao).
    Retorna o objeto inserido (incluindo id) ou None.
    """
    try:
        resp = supabase.table("visitante").insert(data).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print("Erro insert_visitante:", e)
        return None


def insert_escola(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("escola").insert(data).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print("Erro insert_escola:", e)
        return None


def insert_ies(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("ies").insert(data).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print("Erro insert_ies:", e)
        return None


def insert_pesquisador(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        resp = supabase.table("pesquisador").insert(data).execute()
        return resp.data[0] if resp.data else None
    except Exception as e:
        print("Erro insert_pesquisador:", e)
        return None


def get_usuario(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Retorna usuario se existir.
    Nota: para produção, migre para hash de senha (bcrypt) e ajuste aqui.
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
        return resp.data[0] if resp.data else None
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


# -----------------------
# init_db: cria tabelas via psycopg2 (admin) ou orienta execução manual no Supabase
# -----------------------
def init_db():
    """
    Cria tabelas se não existirem.
    Se DATABASE_URL e psycopg2 existirem, cria usando SQL direto.
    Caso contrário, tenta detectar se há service_role e orienta execução no SQL Editor.
    """
    sql_statements = [
        """
        CREATE TABLE IF NOT EXISTS visitante (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            genero TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            endereco TEXT NOT NULL,
            qtd_pessoas INTEGER,
            data DATE NOT NULL,
            turno TEXT NOT NULL,
            tempo_estimado TEXT,
            observacao TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS escola (
            id SERIAL PRIMARY KEY,
            nome_escola TEXT NOT NULL,
            representante TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            endereco TEXT NOT NULL,
            num_alunos INTEGER,
            data DATE NOT NULL,
            turno TEXT NOT NULL,
            observacao TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ies (
            id SERIAL PRIMARY KEY,
            nome_ies TEXT NOT NULL,
            representante TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            endereco TEXT NOT NULL,
            num_alunos INTEGER,
            data DATE NOT NULL,
            turno TEXT NOT NULL,
            observacao TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS pesquisador (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            genero TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            instituicao TEXT NOT NULL,
            pesquisa TEXT NOT NULL,
            data DATE NOT NULL,
            turno TEXT NOT NULL,
            tempo_estimado TEXT,
            observacao TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        );
        """,
        # insere admin se não existir
        """
        INSERT INTO usuarios (username, password, ativo)
        SELECT 'admin','admin',1
        WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE username='admin');
        """,
    ]

    if DATABASE_URL and psycopg2:
        try:
            conn = get_connection()
            cur = conn.cursor()
            for s in sql_statements:
                cur.execute(s)
            conn.commit()
            conn.close()
            print("init_db: tabelas criadas/validadas via DATABASE_URL.")
        except Exception as e:
            print("init_db: erro ao criar tabelas via DATABASE_URL:", e)
    else:
        # tenta criar um cliente admin via SERVICE_ROLE_KEY (se definido)
        admin_client = create_admin_client()
        if admin_client:
            # Observação: o client Admin via PostgREST/HTTP não executa SQL arbitrário.
            # Para criar as tabelas, o caminho correto é executar o SQL Editor do Supabase.
            print("init_db: DATABASE_URL ausente ou psycopg2 não disponível.")
            print("init_db: service_role disponível — recomenda executar os SQLs abaixo no SQL Editor do Supabase:")
            for s in sql_statements:
                print(s)
        else:
            print("init_db: pula criação automática — DATABASE_URL ausente, psycopg2 ausente e service_role não definido.")
            print("init_db: execute os SQLs no SQL Editor do Supabase para criar as tabelas.")


# -----------------------
# Health check utilitário (usa supabase HTTP)
# -----------------------
def health_check() -> bool:
    """
    Testa uma query simples via supabase table 'health' (se existir) ou testa uma pequena select.
    Retorna True se a chamada HTTP ao PostgREST retornar (mesmo sem dados).
    """
    try:
        # tentativa simples contra tabela health (se existir)
        resp = supabase.table("health").select("id").limit(1).execute()
        # se a tabela não existir, resp pode vir sem data mas sem erro HTTP
        return True
    except Exception:
        # fallback: tenta uma chamada simples ao PostgREST para listar tables (pode falhar dependendo das permissões)
        try:
            resp = supabase.table("visitante").select("id").limit(1).execute()
            return True
        except Exception:
            return False