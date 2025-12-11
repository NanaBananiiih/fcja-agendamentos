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
    Valida telefones brasileiros em formatos comuns:

    Exemplos aceitos:
      +55 (83) 99999-8888
      (83) 99999-8888
      83999998888
      83 9999 8888
      999998888

    Regras:
      - opcional +55 ou 55
      - opcional DDD com ou sem parênteses (2 dígitos)
      - número local com 8 ou 9 dígitos, com ou sem hífen
    """
    if not t:
        return False

    s = t.strip()

    pattern = re.compile(r'''
        ^(?:\+?55[\s-]*)?                # +55 ou 55 (opcional)
        (?:\(?\d{2}\)?[\s-]*)?           # DDD opcional
        (?:\d{4,5}[-\s]?\d{4})$          # número (8 ou 9 dígitos)
    ''', re.VERBOSE)

    if pattern.match(s):
        return True

    # fallback: só números (8 a 11 dígitos)
    digits = re.sub(r'\D', '', s)
    return 8 <= len(digits) <= 11

# ---------- Normalização ----------
def normalizar_turno(turno: str) -> str | None:
    """
    Normaliza turno: somente manhã ou tarde.
    """
    t = (turno or "").strip().lower()
    if t in {"manha", "manhã"}:
        return "manhã"
    if t == "tarde":
        return "tarde"
    return None
