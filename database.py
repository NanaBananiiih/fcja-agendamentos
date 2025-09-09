import os, sqlite3
DB_PATH = os.path.join(os.path.dirname(__file__), "fcja.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS visitante (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, genero TEXT, email TEXT NOT NULL,
        telefone TEXT NOT NULL, endereco TEXT, qtd_pessoas INTEGER, data TEXT NOT NULL, turno TEXT NOT NULL,
        tempo_estimado TEXT, observacao TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS escola (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_escola TEXT NOT NULL, representante TEXT NOT NULL, email TEXT NOT NULL,
        telefone TEXT NOT NULL, endereco TEXT, num_alunos INTEGER, data TEXT NOT NULL, turno TEXT NOT NULL, observacao TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_ies TEXT NOT NULL, representante TEXT NOT NULL, email TEXT NOT NULL,
        telefone TEXT NOT NULL, endereco TEXT, num_alunos INTEGER, data TEXT NOT NULL, turno TEXT NOT NULL, observacao TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS pesquisador (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, genero TEXT, email TEXT NOT NULL,
        telefone TEXT NOT NULL, instituicao TEXT, pesquisa TEXT, data TEXT NOT NULL, turno TEXT NOT NULL,
        tempo_estimado TEXT, observacao TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, ativo INTEGER DEFAULT 1)""")
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE username='admin'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO usuarios (username,password,ativo) VALUES ('admin','admin',1)")
    conn.commit(); conn.close()
