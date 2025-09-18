import re
from datetime import datetime

# Formato padrão das datas (YYYY-MM-DD, vindo do input type="date")
DATE_FMT = "%Y-%m-%d"

def _parse(s: str):
    """Converte string em datetime.date no formato padrão."""
    return datetime.strptime(s, DATE_FMT)

# ---------- Validações de data ----------
def validar_data_visita(s: str) -> bool:
    """
    Visitas: terça a domingo (09:00 - 16:00).
    Segunda-feira é fechado.
    """
    try:
        d = _parse(s)
        # weekday(): segunda=0, terça=1 ... domingo=6
        return d.weekday() in [1, 2, 3, 4, 5, 6]  # terça a domingo
    except Exception:
        return False

def validar_data_pesquisa(s: str) -> bool:
    """
    Pesquisas: segunda a sexta (09:00 - 16:00).
    Sábado e domingo não funcionam.
    """
    try:
        d = _parse(s)
        return d.weekday() in [0, 1, 2, 3, 4]  # segunda a sexta
    except Exception:
        return False

# ---------- Validações de contato ----------
def validar_email(e: str) -> bool:
    """Valida formato de e-mail simples."""
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e or "") is not None

def validar_telefone(t: str) -> bool:
    """
    Valida telefones no formato brasileiro:
    - (83) 99999-8888
    - 83 99999-8888
    - 83999998888
    """
    return re.fullmatch(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", t or "") is not None

# ---------- Normalização ----------
def normalizar_turno(turno: str) -> str | None:
    """
    Normaliza o turno informado pelo usuário.
    Aceita: manhã / manha, tarde.
    Retorna 'manhã' ou 'tarde'.
    """
    t = (turno or "").strip().lower()
    if t in {"manha", "manhã"}:
        return "manhã"
    if t == "tarde":
        return "tarde"
    return None
