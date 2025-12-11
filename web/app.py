# web/app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import os, sys
from datetime import datetime, date
from typing import Dict, Any, Optional

# permite importar database.py que está fora da pasta web/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# init_db e get_connection podem não existir se DATABASE_URL não for usado
try:
    from database import init_db, get_connection
except Exception:
    def init_db():
        raise RuntimeError("init_db indisponível (DATABASE_URL/psycopg2 não configurados).")

    def get_connection():
        raise RuntimeError("get_connection indisponível (DATABASE_URL/psycopg2 não configurados).")

# Funções runtime (Supabase)
from database import (
    insert_visitante, insert_escola, insert_ies, insert_pesquisador,
    list_visitantes
)

# Cliente Supabase para listagem dos últimos registros
try:
    from supabase_client import supabase
except Exception:
    supabase = None

from utils.validacoes import (
    validar_email, validar_telefone,
    validar_data_visita, validar_data_pesquisa,
    normalizar_turno
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'fcja-secret')

# -----------------------------------------------------
# Funções utilitárias
# -----------------------------------------------------
def _mask_url(u: str) -> str:
    if not u:
        return ""
    if "://" in u and "@" in u:
        i = u.find("://") + 3
        j = u.rfind("@")
        return u[:i] + "***" + u[j:]
    return u

def _parse_date(d: str) -> Optional[date]:
    if not d:
        return None
    try:
        if "/" in d:
            return datetime.strptime(d, "%d/%m/%Y").date()
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None

def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default

# -----------------------------------------------------
# Inicialização
# -----------------------------------------------------
_boot_done = False

@app.before_request
def _boot_once():
    global _boot_done
    if _boot_done:
        return
    _boot_done = True

    print("Rodando inicialização...")
    print("DATABASE_URL:", _mask_url(os.getenv("DATABASE_URL", "")))

    try:
        init_db()
        print("init_db: ok")
    except Exception as e:
        print("init_db erro (ignorado):", repr(e))

# -----------------------------------------------------
# Rotas principais
# -----------------------------------------------------
@app.get('/')
def index():
    return render_template('index.html')

@app.get('/agendar/<tipo>')
def agendar_form(tipo):
    if tipo not in {'visitante', 'escola', 'ies', 'pesquisador'}:
        return redirect(url_for('index'))
    return render_template('form.html', tipo=tipo)

@app.post('/agendar/<tipo>')
def agendar_submit(tipo):
    if tipo not in {'visitante', 'escola', 'ies', 'pesquisador'}:
        flash('Tipo inválido', 'danger')
        return redirect(url_for('index'))

    print("=== POST agendar ===")
    print("tipo:", tipo)
    print("form:", dict(request.form))

    data = request.form.to_dict()
    turno = normalizar_turno(data.get('turno'))
    data_str = (data.get('data') or '').strip()
    horario_chegada = data.get("horario_chegada")
    duracao = data.get("duracao")  # opcional
    d = _parse_date(data_str)

    print("turno:", turno, "| data:", d, "| chegada:", horario_chegada)

    if not turno:
        flash('Turno inválido', 'danger')
        return redirect(request.url)

    if not d:
        flash('Data inválida', 'danger')
        return redirect(request.url)

    if tipo in {'visitante', 'escola', 'ies'}:
        if not validar_data_visita(data_str):
            flash('Data inválida (visita)', 'danger')
            return redirect(request.url)
    else:
        if not validar_data_pesquisa(data_str):
            flash('Data inválida (pesquisa)', 'danger')
            return redirect(request.url)

    if not validar_email(data.get('email', '')):
        flash('E-mail inválido', 'danger')
        return redirect(request.url)

    if not validar_telefone(data.get('telefone', '')):
        flash('Telefone inválido', 'danger')
        return redirect(request.url)

    if not horario_chegada:
        flash("Informe o horário de chegada.", "danger")
        return redirect(request.url)

    try:
        payload = {}
        novo: Optional[Dict[str, Any]] = None

        # ------------------------------------------
        # VISITANTE
        # ------------------------------------------
        if tipo == 'visitante':
            qtd = safe_int(data.get('qtd_pessoas'), 1)
            payload = {
                "nome": data.get('nome'),
                "genero": data.get('genero'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "endereco": data.get('endereco'),
                "qtd_pessoas": qtd,
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": horario_chegada,
                "duracao": duracao,
                "observacao": data.get('observacao'),
            }
            novo = insert_visitante(payload)

        # ------------------------------------------
        # ESCOLA
        # ------------------------------------------
        elif tipo == 'escola':
            payload = {
                "nome_escola": data.get('nome_escola'),
                "representante": data.get('representante'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "endereco": data.get('endereco'),
                "num_alunos": safe_int(data.get('num_alunos'), 0),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": horario_chegada,
                "duracao": duracao,
                "observacao": data.get('observacao'),
            }
            novo = insert_escola(payload)

        # ------------------------------------------
        # IES
        # ------------------------------------------
        elif tipo == 'ies':
            representante = data.get('representante') or data.get('responsavel')
            payload = {
                "nome_ies": data.get('nome_ies'),
                "representante": representante,
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "endereco": data.get('endereco'),
                "num_alunos": safe_int(data.get('num_alunos'), 0),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": horario_chegada,
                "duracao": duracao,
                "observacao": data.get('observacao'),
            }
            novo = insert_ies(payload)

        # ------------------------------------------
        # PESQUISADOR
        # ------------------------------------------
        else:
            payload = {
                "nome": data.get('nome'),
                "genero": data.get('genero'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "instituicao": data.get('instituicao'),
                "pesquisa": data.get('pesquisa'),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": horario_chegada,
                "duracao": duracao,
                "observacao": data.get('observacao'),
            }
            novo = insert_pesquisador(payload)

        if novo:
            print(f"INSERT OK (supabase): tipo={tipo}, id={novo.get('id')}")
            flash('Agendamento enviado com sucesso!', 'success')
        else:
            print("ERRO INSERT: resposta vazia")
            flash('Erro ao salvar no banco (Supabase).', 'danger')

    except Exception as e:
        print("ERRO INSERT:", e)
        flash('Erro ao salvar no banco.', 'danger')

    return redirect(url_for('index'))

# -----------------------------------------------------
# Últimos registros
# -----------------------------------------------------
@app.get('/ultimos')
def ultimos():
    dados: Dict[str, Any] = {}

    if supabase is not None:
        for t in ['visitante', 'escola', 'ies', 'pesquisador']:
            try:
                resp = supabase.table(t).select("*").order("id", desc=True).limit(5).execute()
                dados[t] = resp.data or []
            except Exception as e:
                print(f"Erro Supabase ({t}):", e)
                dados[t] = []
    else:
        dados = {t: [] for t in ['visitante','escola','ies','pesquisador']}

    return render_template('ultimos.html', dados=dados)


# -----------------------------------------------------
# DIAGNÓSTICO
# -----------------------------------------------------
@app.get('/diag')
def diag():
    key = request.args.get("key")
    if key != "fcja":
        return "forbidden", 403

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database() AS db")
                row = cur.fetchone()
                return {"db": row["db"]}
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == '__main__':
    app.run(debug=True)