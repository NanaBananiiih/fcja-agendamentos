#!/usr/bin/env python3
import os
import argparse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import csv
from pathlib import Path

# Carrega .env localmente (se houver)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrada. Defina a variável de ambiente (Render > External Database URL).")

def get_conn():
    # sslmode=require é recomendado no Render
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)

# ------------------ Ações ------------------

def list_tables():
    """Lista as tabelas do schema public."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name
        """)
        rows = cur.fetchall()
    if not rows:
        print("Nenhuma tabela encontrada no schema 'public'.")
        return
    print("Tabelas em 'public':")
    for r in rows:
        print(" -", r["table_name"])

def show_table(table: str, limit: int = 10):
    """Mostra registros de uma tabela."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT %s", (limit,))
        regs = cur.fetchall()
    if not regs:
        print(f"Nenhum registro encontrado em '{table}'.")
        return
    print(f"=== {table} (últimos {len(regs)}) ===")
    for i, row in enumerate(regs, 1):
        print(f"[{i}]")
        for k, v in row.items():
            print(f"  {k}: {v}")

def export_table(table: str, fmt: str, out: str | None, limit: int | None):
    """Exporta uma tabela para CSV ou JSON."""
    fmt = fmt.lower()
    if fmt not in {"csv", "json"}:
        raise ValueError("Formato inválido. Use csv ou json.")

    # caminho de saída (padrão: ./export/<tabela>.[csv|json])
    export_dir = Path("export")
    export_dir.mkdir(exist_ok=True)
    out_path = Path(out) if out else export_dir / f"{table}.{fmt}"

    sql = f"SELECT * FROM {table} ORDER BY id DESC"
    params = ()
    if isinstance(limit, int) and limit > 0:
        sql += " LIMIT %s"
        params = (limit,)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        regs = cur.fetchall()

    if fmt == "json":
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(regs, f, ensure_ascii=False, indent=2)
    else:  # csv
        if regs:
            headers = list(regs[0].keys())
        else:
            headers = []
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in regs:
                w.writerow(r)

    print(f"Exportado {len(regs)} registro(s) de '{table}' para {out_path.resolve()}")

def export_all(fmt: str, outdir: str | None, limit: int | None):
    """Exporta todas as tabelas do schema public para CSV/JSON."""
    out_base = Path(outdir) if outdir else Path("export")
    out_base.mkdir(parents=True, exist_ok=True)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name
        """)
        tables = [r["table_name"] for r in cur.fetchall()]

    if not tables:
        print("Nenhuma tabela encontrada para exportar.")
        return

    for t in tables:
        dest = out_base / f"{t}.{fmt}"
        export_table(t, fmt, str(dest), limit)

# ------------------ CLI ------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ferramenta de consulta e export do Postgres (Render)."
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
        list_tables()
    elif args.cmd == "show":
        show_table(args.table, args.limit)
    elif args.cmd == "export":
        export_table(args.table, args.fmt, args.out, args.limit)
    elif args.cmd == "export-all":
        export_all(args.fmt, args.outdir, args.limit)

if __name__ == "__main__":
    main()