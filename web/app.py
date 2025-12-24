from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sys
from datetime import datetime, date
from typing import Dict, Any, Optional

# permite importar database.py que está fora da pasta web/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# init_db e get_connection podem não existir se DATABASE_URL não for usado
try:
    from database import init_db, get_connection
except Exception:
    def init_db():
        raise RuntimeError("init_db indisponível.")

    def get_connection():
        raise RuntimeError("get_connection indisponível.")

# Funções runtime (Supabase)
from database import (
    insert_visitante,
    insert_escola,
    insert_ies,
    insert_pesquisador,
    list_visitantes
)

# Cliente Supabase
try:
    from supabase_client import supabase
except Exception:
    supabase = None

from utils.validacoes import (
    validar_email,
    validar_telefone,
    validar_data_visita,
    validar_data_pesquisa,
    normalizar_turno
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "fcja-secret")

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
# Inicialização (executa apenas 1 vez)
# -----------------------------------------------------
_boot_done = False

@app.before_request
def _boot_once():
    global _boot_done
    if _boot_done:
        return
    _boot_done = True

    print("Inicializando aplicação FCJA...")
    print("SUPABASE:", _mask_url(os.getenv("SUPABASE_URL", "")))

    try:
        init_db()
        print("init_db: OK")
    except Exception as e:
        print("init_db ignorado:", e)

# -----------------------------------------------------
# ROTAS PRINCIPAIS
# -----------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/agendar/<tipo>")
def agendar_form(tipo):
    if tipo not in {"visitante", "escola", "ies", "pesquisador"}:
        return redirect(url_for("index"))
    return render_template("form.html", tipo=tipo)


@app.post("/agendar/<tipo>")
def agendar_submit(tipo):
    if tipo not in {"visitante", "escola", "ies", "pesquisador"}:
        flash("Tipo inválido", "danger")
        return redirect(url_for("index"))

    data = request.form.to_dict()
    turno = normalizar_turno(data.get("turno"))
    data_str = (data.get("data") or "").strip()
    d = _parse_date(data_str)

    if not turno:
        flash("Turno inválido", "danger")
        return redirect(request.url)

    if not d:
        flash("Data inválida", "danger")
        return redirect(request.url)

    if tipo in {"visitante", "escola", "ies"}:
        if not validar_data_visita(data_str):
            flash("Data inválida para visita", "danger")
            return redirect(request.url)
    else:
        if not validar_data_pesquisa(data_str):
            flash("Data inválida para pesquisa", "danger")
            return redirect(request.url)

    if not validar_email(data.get("email", "")):
        flash("E-mail inválido", "danger")
        return redirect(request.url)

    if not validar_telefone(data.get("telefone", "")):
        flash("Telefone inválido", "danger")
        return redirect(request.url)

    try:
        novo = None

        if tipo == "visitante":
            novo = insert_visitante({
                "nome": data.get("nome"),
                "genero": data.get("genero"),
                "email": data.get("email"),
                "telefone": data.get("telefone"),
                "endereco": data.get("endereco"),
                "qtd_pessoas": safe_int(data.get("qtd_pessoas"), 1),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": data.get("horario_chegada"),
                "duracao": data.get("duracao"),
                "observacao": data.get("observacao"),
            })

        elif tipo == "escola":
            novo = insert_escola({
                "nome_escola": data.get("nome_escola"),
                "representante": data.get("representante"),
                "email": data.get("email"),
                "telefone": data.get("telefone"),
                "endereco": data.get("endereco"),
                "num_alunos": safe_int(data.get("num_alunos"), 0),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": data.get("horario_chegada"),
                "duracao": data.get("duracao"),
                "observacao": data.get("observacao"),
            })

        elif tipo == "ies":
            novo = insert_ies({
                "nome_ies": data.get("nome_ies"),
                "representante": data.get("representante") or data.get("responsavel"),
                "email": data.get("email"),
                "telefone": data.get("telefone"),
                "endereco": data.get("endereco"),
                "num_alunos": safe_int(data.get("num_alunos"), 0),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": data.get("horario_chegada"),
                "duracao": data.get("duracao"),
                "observacao": data.get("observacao"),
            })

        else:  # pesquisador
            novo = insert_pesquisador({
                "nome": data.get("nome"),
                "genero": data.get("genero"),
                "email": data.get("email"),
                "telefone": data.get("telefone"),
                "instituicao": data.get("instituicao"),
                "pesquisa": data.get("pesquisa"),
                "data": d.isoformat(),
                "turno": turno,
                "horario_chegada": data.get("horario_chegada"),
                "duracao": data.get("duracao"),
                "observacao": data.get("observacao"),
            })

        if novo:
            flash("Agendamento enviado com sucesso!", "success")
        else:
            flash("Erro ao salvar no banco.", "danger")

    except Exception as e:
        print("Erro:", e)
        flash("Erro interno ao salvar.", "danger")

    return redirect(url_for("index"))

# -----------------------------------------------------
# ÚLTIMOS REGISTROS (ADMIN)
# -----------------------------------------------------
@app.get("/ultimos")
def ultimos():
    dados: Dict[str, Any] = {}

    if supabase:
        for t in ["visitante", "escola", "ies", "pesquisador"]:
            try:
                resp = supabase.table(t).select("*").order("id", desc=True).limit(5).execute()
                dados[t] = resp.data or []
            except Exception:
                dados[t] = []
    else:
        dados = {t: [] for t in ["visitante", "escola", "ies", "pesquisador"]}

    return render_template("ultimos.html", dados=dados)

# -----------------------------------------------------
# 🔥 HEALTH CHECK (PING)
# -----------------------------------------------------
@app.get("/health")
def health():
    """
    Endpoint usado para manter a aplicação e o Supabase ativos.
    """
    return {"status": "ok"}, 200

# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)