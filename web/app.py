from flask import Flask, render_template, request, redirect, url_for, flash
import os, sys

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

# Inicializa o schema no primeiro request do app
@app.before_first_request
def _boot():
    print("Rodando inicialização ao iniciar o app")
    init_db()

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

    if tipo in {'visitante','escola','ies'}:
        if not validar_data_visita(data.get('data','')):
            flash('Data inválida (visita)','danger')
            return redirect(request.url)
    else:
        if not validar_data_pesquisa(data.get('data','')):
            flash('Data inválida (pesquisa)','danger')
            return redirect(request.url)

    if not validar_email(data.get('email','')):
        flash('E-mail inválido','danger')
        return redirect(request.url)

    if not validar_telefone(data.get('telefone','')):
        flash('Telefone inválido','danger')
        return redirect(request.url)

    # Insere conforme o tipo
    with get_connection() as conn:
        with conn.cursor() as cur:
            if tipo == 'visitante':
                cur.execute(
                    """
                    INSERT INTO visitante
                      (nome, genero, email, telefone, endereco, qtd_pessoas, data, turno, tempo_estimado, observacao)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        data.get('nome'),
                        data.get('genero'),
                        data.get('email'),
                        data.get('telefone'),
                        data.get('endereco'),
                        int(data.get('qtd_pessoas') or 1),
                        data.get('data'),
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
                    """,
                    (
                        data.get('nome_escola'),
                        data.get('representante'),
                        data.get('email'),
                        data.get('telefone'),
                        data.get('endereco'),
                        int(data.get('num_alunos') or 0),
                        data.get('data'),
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
                    """,
                    (
                        data.get('nome_ies'),
                        data.get('representante'),
                        data.get('email'),
                        data.get('telefone'),
                        data.get('endereco'),
                        int(data.get('num_alunos') or 0),
                        data.get('data'),
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
                    """,
                    (
                        data.get('nome'),
                        data.get('genero'),
                        data.get('email'),
                        data.get('telefone'),
                        data.get('instituicao'),
                        data.get('pesquisa'),
                        data.get('data'),
                        turno,
                        data.get('tempo_estimado'),
                        data.get('observacao')
                    )
                )
        conn.commit()

    flash('Agendamento enviado com sucesso!','success')
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

if __name__ == '__main__':
    # Em produção (Render) quem roda é o gunicorn; localmente pode usar flask run ou python app.py
    app.run(debug=True)