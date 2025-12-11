#!/usr/bin/env python3
"""
consultar.py — Ferramenta de consulta e export usando Supabase (principal)
Se possível usa supabase-py (anon key). Para listar todas as tabelas
(information_schema) usa psycopg2 como fallback administrativo.
"""
import os
import argparse
from dotenv import load_dotenv
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Carrega .env localmente (se houver)
load_dotenv()

# Importa supabase client (crie supabase_client.py conforme instruído)
from supabase_client import supabase

# Importa psycopg2 apenas para operações administrativas (fallback)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None  # pode não existir no ambiente cliente (ok)


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Se não tiver DATABASE_URL, ainda podemos usar supabase para tabelas conhecidas
    # mas operações administrativas dependerão do DATABASE_URL/psycopg2.
    print("Aviso: DATABASE_URL não encontrada. Operações administrativas podem falhar.")

# ------------------ Helpers ------------------

def get_conn():
    """Retorna conexão psycopg2 (fallback administrativo)."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida (necessária para operações admin).")
    if not psycopg2:
        raise RuntimeError("psycopg2 não instalado no ambiente (necessário para operações admin).")
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)


def known_tables() -> List[str]:
    """Lista de tabelas que sabemos existir no projeto (fallback sem information_schema)."""
    return ["visitante", "escola", "ies", "pesquisador", "usuarios", "health"]


# ------------------ Ações ------------------

def list_tables() -> List[str]:
    """
    Lista as tabelas do schema public.
    Primeiro tenta via psycopg2 -> information_schema (mais confiável).
    Se não for possível, retorna a lista 'known_tables' como fallback.
    """
    if psycopg2 and DATABASE_URL:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema='public'
                    ORDER BY table_name
                """)
                rows = cur.fetchall()
            tables = [r["table_name"] for r in rows]
            return tables
        except Exception as e:
            print("Falha ao consultar information_schema (fallback para known_tables):", e)

    # fallback
    return known_tables()


def show_table(table: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Mostra registros de uma tabela usando Supabase (PostgREST).
    Retorna a lista de registros (cada um como dict).
    """
    try:
        # usa order e limit via supabase-py
        resp = supabase.table(table).select("*").order("id", desc=True).limit(limit).execute()
        data = resp.data or []
        # Supabase já retorna dicionários compatíveis
        for i, row in enumerate(data, start=1):
            print(f"[{i}]")
            for k, v in row.items():
                print(f"  {k}: {v}")
        return data
    except Exception as e:
        print(f"Erro ao consultar tabela '{table}' via Supabase:", e)
        # fallback: tentar via psycopg2 se disponível
        if psycopg2 and DATABASE_URL:
            try:
                with get_conn() as conn, conn.cursor() as cur:
                    cur.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT %s", (limit,))
                    regs = cur.fetchall()
                for i, row in enumerate(regs, start=1):
                    print(f"[{i}]")
                    for k, v in row.items():
                        print(f"  {k}: {v}")
                return regs
            except Exception as e2:
                print("Fallback psycopg2 também falhou:", e2)
        return []


def export_table(table: str, fmt: str, out: Optional[str], limit: Optional[int]):
    """
    Exporta uma tabela para CSV ou JSON usando Supabase como primeira opção.
    """
    fmt = fmt.lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("Formato inválido. Use csv ou json.")

    export_dir = Path("export")
    export_dir.mkdir(exist_ok=True)
    out_path = Path(out) if out else export_dir / f"{table}.{fmt}"

    # monta query via supabase (usa limit se passado)
    try:
        q = supabase.table(table).select("*").order("id", desc=True)
        if isinstance(limit, int) and limit > 0:
            q = q.limit(limit)
        resp = q.execute()
        regs = resp.data or []
    except Exception as e:
        print(f"Erro ao exportar '{table}' via Supabase, tentando fallback psycopg2: {e}")
        # fallback psycopg2
        if psycopg2 and DATABASE_URL:
            with get_conn() as conn, conn.cursor() as cur:
                sql = f"SELECT * FROM {table} ORDER BY id DESC"
                params = ()
                if isinstance(limit, int) and limit > 0:
                    sql += " LIMIT %s"
                    params = (limit,)
                cur.execute(sql, params)
                regs = cur.fetchall()
        else:
            regs = []

    # grava arquivo
    if fmt == "json":
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(regs, f, ensure_ascii=False, indent=2)
    else:  # csv
        if regs:
            # regs pode ser lista de dicts (supabase) ou RealDictRow (psycopg2) — ambos mapeáveis
            headers = list(regs[0].keys())
        else:
            headers = []
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in regs:
                w.writerow(r)

    print(f"Exportado {len(regs)} registro(s) de '{table}' para {out_path.resolve()}")


def export_all(fmt: str, outdir: Optional[str], limit: Optional[int]):
    """
    Exporta todas as tabelas do schema public para CSV/JSON.
    Usa psycopg2->information_schema para obter a lista de tabelas, se possível.
    """
    out_base = Path(outdir) if outdir else Path("export")
    out_base.mkdir(parents=True, exist_ok=True)

    tables = []
    if psycopg2 and DATABASE_URL:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema='public'
                    ORDER BY table_name
                """)
                tables = [r["table_name"] for r in cur.fetchall()]
        except Exception as e:
            print("Falha ao listar tables via information_schema (fallback):", e)

    if not tables:
        tables = known_tables()

    if not tables:
        print("Nenhuma tabela encontrada para exportar.")
        return

    for t in tables:
        dest = out_base / f"{t}.{fmt}"
        export_table(t, fmt, str(dest), limit)


# ------------------ CLI ------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ferramenta de consulta e export do Postgres/Supabase."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # listar tabelas
    p_list = sub.add_parser("list", help="Lista todas as tabelas do schema public.")

    # mostrar registros
    p_show = sub.add_parser("show", help="Mostra registros de uma tabela.")
    p_show.add_argument("table", help="Nome da tabela (ex: visitante, escola, ies, pesquisador, usuarios)")
    p_show.add_argument("--limit", "-n", type=int, default=10, help="Quantidade de registros (default: 10)")

    # exportar tabela
    p_exp = sub.add_parser("export", help="Exporta uma tabela para CSV ou JSON.")
    p_exp.add_argument("table", help="Nome da tabela")
    p_exp.add_argument("--fmt", choices=["csv", "json"], default="csv", help="Formato (csv/json)")
    p_exp.add_argument("--out", help="Arquivo de saída (padrão: export/<tabela>.<fmt>)")
    p_exp.add_argument("--limit", "-n", type=int, help="Limite de registros (opcional)")

    # exportar todas
    p_all = sub.add_parser("export-all", help="Exporta TODAS tabelas para CSV/JSON.")
    p_all.add_argument("--fmt", choices=["csv", "json"], default="csv", help="Formato (csv/json)")
    p_all.add_argument("--outdir", help="Pasta de saída (padrão: ./export)")
    p_all.add_argument("--limit", "-n", type=int, help="Limite de registros (opcional)")

    args = parser.parse_args()

    if args.cmd == "list":
        tables = list_tables()
        if not tables:
            print("Nenhuma tabela encontrada.")
        else:
            print("Tabelas em 'public':")
            for t in tables:
                print(" -", t)
    elif args.cmd == "show":
        show_table(args.table, args.limit)
    elif args.cmd == "export":
        export_table(args.table, args.fmt, args.out, args.limit)
    elif args.cmd == "export-all":
        export_all(args.fmt, args.outdir, args.limit)


if __name__ == "__main__":
    main()