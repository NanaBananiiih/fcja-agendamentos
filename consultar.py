# consultar.py
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Tenta carregar variáveis do .env se a lib estiver instalada
try:
    from dotenv import load_dotenv  # python-dotenv
    load_dotenv()
except Exception:
    pass

# 1) URL via .env (recomendado): defina DATABASE_URL no .env
# 2) Fallback: URL fixa aqui no código (use apenas para testes locais)
HARDCODED_URL = (
    "postgresql://fcja_postgres_user:7C6AbuEPCTu1Bj2xRJxGUA2c2kAiDuT0@"
    "dpg-d33lahbipnbc73e3ngmg-a.oregon-postgres.render.com/fcja_postgres"
)

def get_database_url() -> str:
    """Retorna a URL do banco, priorizando .env; se não houver, usa o fallback."""
    url = os.getenv("DATABASE_URL")
    if url and url.strip():
        return url.strip()
    if HARDCODED_URL and HARDCODED_URL.strip():
        return HARDCODED_URL.strip()
    raise RuntimeError(
        "DATABASE_URL não definido. Configure no .env ou preencha HARDCODED_URL."
    )

def get_connection():
    """Abre conexão com sslmode=require (necessário no Render)."""
    url = get_database_url()
    
    return psycopg2.connect(url, sslmode="require", cursor_factory=RealDictCursor)

def consultar_tabela(tabela: str = "visitante", limite: int = 10):
    """Consulta os 'limite' últimos registros da tabela informada (por id DESC)."""
    sql = f'SELECT * FROM "{tabela}" ORDER BY id DESC LIMIT %s;'
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limite,))
            return cur.fetchall()

def imprimir_registros(registros):
    if not registros:
        print("→ Nenhum registro encontrado.")
        return
    for i, row in enumerate(registros, start=1):
       
        print(f"\n#{i}")
        for k, v in row.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    # Uso opcional: python consultar.py [tabela] [limite]
    tabela = sys.argv[1] if len(sys.argv) > 1 else "visitante"
    try:
        limite = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    except ValueError:
        limite = 10

    try:
        print(f"Consultando tabela '{tabela}' (limite {limite})…")
        registros = consultar_tabela(tabela, limite)
        imprimir_registros(registros)
    except Exception as e:
        print("❌ Erro ao consultar:", e)