# consultar.py
import os
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor

# Opcional: carrega .env se existir (não falha se não existir)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 1) DATABASE_URL por .env (Render) OU fallback local
DATABASE_URL = os.getenv("DATABASE_URL") or (
    # >>> Se quiser, cole sua URL do Render aqui para fallback:
    # "postgresql://usuario:senha@host:5432/nome_banco"
    ""
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não encontrada. "
        "Defina no .env ou preencha o fallback no arquivo."
    )

def get_conn():
    # no Render o Postgres exige SSL
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)

def list_tables():
    """Lista todas as tabelas do schema public."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            rows = cur.fetchall()
            if not rows:
                print("Nenhuma tabela encontrada no schema 'public'.")
                return
            print("Tabelas em 'public':")
            for r in rows:
                print(f"- {r['table_name']}")

def show_table(table: str, limit: int):
    """Mostra registros de uma tabela específica."""
    # proteção simples de nome de tabela
    allowed = {"visitante", "escola", "ies", "pesquisador", "usuarios"}
    if table not in allowed:
        print(f"Tabela '{table}' não é permitida. Use uma destas: {', '.join(sorted(allowed))}")
        return

    with get_conn() as conn:
        with conn.cursor() as cur:
            # Ordena por id se existir a coluna
            cur.execute(f"""
                SELECT *
                FROM {table}
                ORDER BY 1 DESC
                LIMIT %s;
            """, (limit,))
            rows = cur.fetchall()

            if not rows:
                print(f"Nenhum registro encontrado em '{table}'.")
                return

            print(f"Registros em '{table}' (máx {limit}):")
            for i, r in enumerate(rows, start=1):
                print(f"\n#{i}")
                for k, v in r.items():
                    print(f"  {k}: {v}")

def main():
    parser = argparse.ArgumentParser(
        description="Ferramenta de consulta ao Postgres (Render)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # consultar.py list
    sub.add_parser("list", help="Lista todas as tabelas do schema public.")

    # consultar.py show <tabela> [--limit 10]
    p_show = sub.add_parser("show", help="Mostra registros de uma tabela.")
    p_show.add_argument("table", help="Tabela (visitante, escola, ies, pesquisador, usuarios)")
    p_show.add_argument("--limit", type=int, default=10, help="Quantidade de registros (default: 10)")

    args = parser.parse_args()

    if args.cmd == "list":
        list_tables()
    elif args.cmd == "show":
        show_table(args.table, args.limit)

if __name__ == "__main__":
    main()