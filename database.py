from dotenv import load_dotenv
load_dotenv()
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Pegue a External Database URL no Render (Info > External Database URL)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL não encontrada. Defina a variável de ambiente com a External Database URL do Postgres (Render)."
    )

def get_connection():
    # sslmode=require é importante no Render
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # --- Tabelas ---
    cur.execute("""
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
        )
    """)

    cur.execute("""
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
        )
    """)

    cur.execute("""
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
        )
    """)

    cur.execute("""
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
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    """)

    # Usuário admin
    cur.execute("SELECT COUNT(*) AS count FROM usuarios WHERE username = 'admin'")
    if cur.fetchone()["count"] == 0:
        cur.execute("INSERT INTO usuarios (username, password, ativo) VALUES ('admin','admin',1)")

    conn.commit()
    conn.close()