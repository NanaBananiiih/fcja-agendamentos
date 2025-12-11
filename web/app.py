# web/app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import os, sys
from datetime import datetime, date
from typing import Dict, Any, Optional

# permite importar database.py que está fora da pasta web/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Mantemos init_db() + get_connection() para operações admin / fallback
from database import init_db, get_connection
# Funções de runtime que usam Supabase (inserções / consultas)
from database import (
    insert_visitante, insert_escola, insert_ies, insert_pesquisador,
    list_visitantes
)

# Importa supabase client para consultas genéricas (ultimos registros)
from supabase_client import supabase

from utils.validacoes import (
    validar_email, validar_telefone,
    validar_data_visita, validar_data_pesquisa,
    normalizar_turno
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'fcja-secret')  # permite override por env

# ---------- utilidades ----------
def _mask_url(u: str) -> str:
    if not u:
        return ""
    if "://" in u and "@" in u:
        i = u.find("://") + 3
        j = u.rfind("@")
        return u[:i] + "***" + u[j:]
    return u

def _parse_date(d: str) -> Optional[date]:
    """Aceita 'YYYY-MM-DD' (input type=date) ou 'DD/MM/YYYY' e retorna date."""
    if not d:
        return None
    try:
        if "/" in d:
            return datetime.strptime(d, "%d/%m/%Y").date()
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None

# ---------- inicialização (compatível Flask 3) ----------
_boot_done = False

@app.before_request
def _boot_once():
    """Executa init_db() apenas na primeira requisição do processo."""
    global _boot_done
    if _boot_done:
        return
    _boot_done = True
    print("Rodando inicialização ao iniciar o app")
    print("DATABASE_URL:", _mask_url(os.getenv("DATABASE_URL", "")))
    try:
        init_db()
        print("init_db: ok")
    except Exception as e:
        print("init_db erro:", repr(e))

# ---------- rotas ----------
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

    print("=== POST agendar ===")
    print("tipo:", tipo)
    print("form:", dict(request.form))

    data = request.form.to_dict()
    turno = normalizar_turno(data.get('turno'))
    data_str = (data.get('data') or '').strip()
    d = _parse_date(data_str)
    print("normalizado turno:", turno, "| data_str:", data_str, "| parsed:", d)

    if not turno:
        print("FAIL: turno inválido")
        flash('Turno inválido','danger'); return redirect(request.url)
    if not d:
        print("FAIL: data inválida")
        flash('Data inválida','danger'); return redirect(request.url)

    if tipo in {'visitante','escola','ies'}:
        if not validar_data_visita(data_str):
            print("FAIL: validar_data_visita")
            flash('Data inválida (visita)','danger'); return redirect(request.url)
    else:
        if not validar_data_pesquisa(data_str):
            print("FAIL: validar_data_pesquisa")
            flash('Data inválida (pesquisa)','danger'); return redirect(request.url)

    if not validar_email(data.get('email','')):
        print("FAIL: email inválido")
        flash('E-mail inválido','danger'); return redirect(request.url)
    if not validar_telefone(data.get('telefone','')):
        print("FAIL: telefone inválido")
        flash('Telefone inválido','danger'); return redirect(request.url)

    try:
        # usa as funções do database.py que invocam supabase (runtime)
        novo: Optional[Dict[str, Any]] = None

        if tipo == 'visitante':
            payload = {
                "nome": data.get('nome'),
                "genero": data.get('genero'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "endereco": data.get('endereco'),
                "qtd_pessoas": int(data.get('qtd_pessoas') or 1),
                "data": d.isoformat(),
                "turno": turno,
                "tempo_estimado": data.get('tempo_estimado'),
                "observacao": data.get('observacao'),
            }
            novo = insert_visitante(payload)

        elif tipo == 'escola':
            payload = {
                "nome_escola": data.get('nome_escola'),
                "representante": data.get('representante'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "endereco": data.get('endereco'),
                "num_alunos": int(data.get('num_alunos') or 0),
                "data": d.isoformat(),
                "turno": turno,
                "observacao": data.get('observacao'),
            }
            novo = insert_escola(payload)

        elif tipo == 'ies':
            payload = {
                "nome_ies": data.get('nome_ies'),
                "representante": data.get('representante'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "endereco": data.get('endereco'),
                "num_alunos": int(data.get('num_alunos') or 0),
                "data": d.isoformat(),
                "turno": turno,
                "observacao": data.get('observacao'),
            }
            novo = insert_ies(payload)

        else:  # pesquisador
            payload = {
                "nome": data.get('nome'),
                "genero": data.get('genero'),
                "email": data.get('email'),
                "telefone": data.get('telefone'),
                "instituicao": data.get('instituicao'),
                "pesquisa": data.get('pesquisa'),
                "data": d.isoformat(),
                "turno": turno,
                "tempo_estimado": data.get('tempo_estimado'),
                "observacao": data.get('observacao'),
            }
            novo = insert_pesquisador(payload)

        if novo:
            nid = novo.get("id") if isinstance(novo, dict) else None
            print(f"INSERT OK (supabase): tipo={tipo} id={nid} payload={payload}")
            flash('Agendamento enviado com sucesso!','success')
        else:
            # resposta vazia ou erro tratado dentro das funções insert_*
            print("ERRO INSERT: resposta vazia do supabase (ver logs das funções insert_*)")
            flash('Erro ao salvar no banco (Supabase). Veja os logs.', 'danger')

    except Exception as e:
        print("ERRO INSERT (exception):", repr(e))
        flash('Erro ao salvar no banco. Veja os logs.', 'danger')

    return redirect(url_for('index'))

@app.get('/ultimos')
def ultimos():
    dados: Dict[str, Any] = {}
    # Primeiro tentamos via Supabase (runtime)
    for t in ['visitante','escola','ies','pesquisador']:
        try:
            resp = supabase.table(t).select("*").order("id", desc=True).limit(5).execute()
            dados[t] = resp.data or []
        except Exception as e:
            print(f"Supabase fetch failed for {t}: {e}")
            # fallback para psycopg2
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 5")
                        dados[t] = cur.fetchall()
            except Exception as e2:
                print(f"Fallback psycopg2 also failed for {t}: {e2}")
                dados[t] = []

    return render_template('ultimos.html', dados=dados)

# (opcional) diagnóstico temporário
@app.get('/diag')
def diag():
    key = request.args.get("key")
    if key != "fcja":
        return "forbidden", 403
    # diag intentionally uses database URL/psycopg2 (admin)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database() AS db, inet_server_addr() AS host, inet_server_port() AS port")
                row = cur.fetchone()
                def count(t):
                    cur.execute(f"SELECT COUNT(*) AS c FROM {t}")
                    return cur.fetchone()["c"]
                return {
                    "db": row["db"], "host": str(row["host"]), "port": row["port"],
                    "visitante": count("visitante"),
                    "escola": count("escola"),
                    "ies": count("ies"),
                    "pesquisador": count("pesquisador"),
                    "usuarios": count("usuarios"),
                }
    except Exception as e:
        print("diag error:", repr(e))
        return {"error": str(e)}, 500

if __name__ == '__main__':
    # modo de desenvolvimento local
    app.run(debug=True)