from database import get_connection
from utils.validacoes import validar_email, validar_telefone, validar_data_visita, normalizar_turno
def cadastrar_visitante(data):
    if not validar_email(data.get('email','')): raise ValueError('E-mail inválido')
    if not validar_telefone(data.get('telefone','')): raise ValueError('Telefone inválido')
    if not validar_data_visita(data.get('data','')): raise ValueError('Data inválida (terça-dom)')
    t = normalizar_turno(data.get('turno','')); 
    if not t: raise ValueError('Turno inválido')
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""INSERT INTO visitante (nome,genero,email,telefone,endereco,qtd_pessoas,data,turno,tempo_estimado,observacao)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", (
        data.get('nome'), data.get('genero'), data.get('email'), data.get('telefone'),
        data.get('endereco'), int(data.get('qtd_pessoas') or 1), data.get('data'), t,
        data.get('tempo_estimado'), data.get('observacao')
    ))
    conn.commit(); conn.close()
def listar(limit=50):
    conn = get_connection(); cur = conn.cursor()
    rows = cur.execute('SELECT * FROM visitante ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    cols = [d[0] for d in cur.description]; conn.close(); return cols, rows
