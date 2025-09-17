from flask import Flask, render_template, request, redirect, url_for, flash
import os, sys
from datetime import datetime

# permite importar database.py que está fora da pasta web/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import init_db, get_connection
from utils.validacoes import (
    validar_email, validar_telefone,
    validar_data_visita, validar_data_pesquisa,
    normalizar_turno
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fcja-secret'

# ---- util: mascarar database url no log ----
def _mask_url(u: str) -> str:
    if not u: return ""
    if "://" in u and "@" in u:
        i = u.find("://") + 3
        j = u.rfind("@")
        return u[:i] + "***" + u[j:]
    return u

def _parse_date(d: str) -> datetime.date | None:
    if not d:
        return None
    try:
        # aceita "YYYY-MM-DD" (type=date) ou "DD/MM/YYYY" (caso algum form esteja assim)
        if "/" in d:
            return datetime.strptime(d, "%d/%m/%Y").date()
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None

# Inicializa o schema no primeiro request do app
@app.before_first_request
def _boot():
    print("Rodando inicialização ao iniciar o app")
    print("DATABASE_URL:", _mask_url(os.getenv("DATABASE_URL", "")))
    try:
        init_db()
    except Exception as e:
        print("init_db erro:", repr(e))

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/agendar/<tipo>')
def agendar_form(tipo):
    if tipo not in {'visitante','escola','ies','pesquisador'}:
        return redirect(url_for('index'))
    return render_template('form.html', tipo=tipo)

@app.post('/agendar/<tipo>')
def agendar_submit(tipo):
    if tipo not in {'visitante','escola','ies','pesquisador'}:
        flash('Tipo inválido','danger')
        return redirect(url_for('index'))

    data = request.form.to_dict()
    turno = normalizar_turno(data.get('turno'))
    if not turno:
        flash('Turno inválido','danger')
        return redirect(request.url)

    # validação por tipo + parse da data
    data_str = data.get('data','').strip()
    if tipo in {'visitante','escola','ies'}:
        if not validar_data_visita(data_str):
            flash('Data inválida (visita)','danger'); return redirect(request.url)
    else:
        if not validar_data_pesquisa(data_str):
            flash('Data inválida (pesquisa)','danger'); return redirect(request.url)

    data_sql = _parse_date(data_str)
    if not data_sql:
        flash('Formato de data inválido','danger'); return redirect(request.url)

    if not validar_email(data.get('email','')):
        flash('E-mail inválido','danger'); return redirect(request.url)
    if not validar_telefone(data.get('telefone','')):
        flash('Telefone inválido','danger'); return redirect(request.url)

    # Insere conforme o tipo
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if tipo == 'visitante':
                    cur.execute(
                        """
                        INSERT INTO visitante
                          (nome, genero, email, telefone, endereco, qtd_pessoas, data, turno, tempo_estimado, observacao)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id
                        """,
                        (
                            data.get('nome'),
                            data.get('genero'),
                            data.get('email'),
                            data.get('telefone'),
                            data.get('endereco'),
                            int(data.get('qtd_pessoas') or 1),
                            data_sql,
                            turno,
                            data.get('tempo_estimado'),
                            data.get('observacao')
                        )
                    )
                elif tipo == 'escola':
                    cur.execute(
                        """
                        INSERT INTO escola
                          (nome_escola, representante, email, telefone, endereco, num_alunos, data, turno, observacao)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id
                        """,
                        (
                            data.get('nome_escola'),
                            data.get('representante'),
                            data.get('email'),
                            data.get('telefone'),
                            data.get('endereco'),
                            int(data.get('num_alunos') or 0),
                            data_sql,
                            turno,
                            data.get('observacao')
                        )
                    )
                elif tipo == 'ies':
                    cur.execute(
                        """
                        INSERT INTO ies
                          (nome_ies, representante, email, telefone, endereco, num_alunos, data, turno, observacao)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id
                        """,
                        (
                            data.get('nome_ies'),
                            data.get('representante'),
                            data.get('email'),
                            data.get('telefone'),
                            data.get('endereco'),
                            int(data.get('num_alunos') or 0),
                            data_sql,
                            turno,
                            data.get('observacao')
                        )
                    )
                else:  # pesquisador
                    cur.execute(
                        """
                        INSERT INTO pesquisador
                          (nome, genero, email, telefone, instituicao, pesquisa, data, turno, tempo_estimado, observacao)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id
                        """,
                        (
                            data.get('nome'),
                            data.get('genero'),
                            data.get('email'),
                            data.get('telefone'),
                            data.get('instituicao'),
                            data.get('pesquisa'),
                            data_sql,
                            turno,
                            data.get('tempo_estimado'),
                            data.get('observacao')
                        )
                    )
                new_id = cur.fetchone()[0]
                print(f"INSERT OK: tipo={tipo} id={new_id}")
        flash('Agendamento enviado com sucesso!','success')
    except Exception as e:
        print("ERRO INSERT:", repr(e))
        flash('Erro ao salvar no banco. Veja os logs.', 'danger')

    return redirect(url_for('index'))

@app.get('/ultimos')
def ultimos():
    dados = {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            for t in ['visitante','escola','ies','pesquisador']:
                cur.execute(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 5")
                dados[t] = cur.fetchall()  # RealDictCursor => lista de dicts
    return render_template('ultimos.html', dados=dados)

# --- Diagnóstico temporário (remova depois) ---
@app.get('/diag')
def diag():
    key = request.args.get("key")
    if key != "fcja":
        return "forbidden", 403
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), inet_server_addr(), inet_server_port()")
            db, host, port = cur.fetchone().values()
            def count(t):
                cur.execute(f"SELECT COUNT(*) AS c FROM {t}")
                return cur.fetchone()["c"]
            return {
                "db": db, "host": str(host), "port": port,
                "visitante": count("visitante"),
                "escola": count("escola"),
                "ies": count("ies"),
                "pesquisador": count("pesquisador"),
                "usuarios": count("usuarios"),
            }

if __name__ == '__main__':
    app.run(debug=True)