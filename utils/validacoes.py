import re
from datetime import datetime

DATE_FMT_1 = "%Y-%m-%d"   # 2025-09-18
DATE_FMT_2 = "%d/%m/%Y"   # 18/09/2025

def _parse_any(s: str):
    s = (s or "").strip()
    for fmt in (DATE_FMT_1, DATE_FMT_2):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    raise ValueError("formato de data inválido")

def validar_data_visita(s):
    """Visitas: terça(1) a domingo(6). Segunda(0) não."""
    try:
        return _parse_any(s).weekday() in [1,2,3,4,5,6]
    except Exception:
        return False

def validar_data_pesquisa(s):
    """Pesquisa: segunda(0) a sexta(4)."""
    try:
        return _parse_any(s).weekday() in [0,1,2,3,4]
    except Exception:
        return False

def validar_email(e):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e or "") is not None

def validar_telefone(t):
    # aceita (83) 99999-9999, 83999999999, 9999-9999 (com DDD)
    return re.fullmatch(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", t or "") is not None

def normalizar_turno(turno):
    t = (turno or "").strip().lower()
    if t in {"manha", "manhã"}: return "manhã"
    if t == "tarde": return "tarde"
    return None
