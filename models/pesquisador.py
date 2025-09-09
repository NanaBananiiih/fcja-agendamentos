from database import get_connection
from utils.validacoes import validar_email, validar_telefone, validar_data_pesquisa, normalizar_turno
def cadastrar_pesquisador(data):
    if not validar_email(data.get('email','')): raise ValueError('E-mail inválido')
    if not validar_telefone(data.get('telefone','')): raise ValueError('Telefone inválido')
    if not validar_data_pesquisa(data.get('data','')): raise ValueError('Data inválida (seg-sex)')
    t = normalizar_turno(data.get('turno','')); 
    if not t: raise ValueError('Turno inválido')
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""INSERT INTO pesquisador (nome,genero,email,telefone,instituicao,pesquisa,data,turno,tempo_estimado,observacao)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", (
        data.get('nome'), data.get('genero'), data.get('email'), data.get('telefone'),
        data.get('instituicao'), data.get('pesquisa'), data.get('data'), t, data.get('tempo_estimado'), data.get('observacao')
    ))
    conn.commit(); conn.close()
def listar(limit=50):
    conn = get_connection(); cur = conn.cursor()
    rows = cur.execute('SELECT * FROM pesquisador ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    cols = [d[0] for d in cur.description]; conn.close(); return cols, rows
