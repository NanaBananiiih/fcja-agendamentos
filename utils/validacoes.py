import re
from datetime import datetime
DATE_FMT = "%Y-%m-%d"
def _parse(s): return datetime.strptime(s, DATE_FMT)
def validar_data_visita(s):
    try: return _parse(s).weekday() in [1,2,3,4,5,6]
    except: return False
def validar_data_pesquisa(s):
    try: return _parse(s).weekday() in [0,1,2,3,4]
    except: return False
def validar_email(e): return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e or "") is not None
def validar_telefone(t): return re.fullmatch(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", t or "") is not None
def normalizar_turno(turno):
    t = (turno or "").strip().lower()
    if t in {"manha","manhã"}: return "manhã"
    if t == "tarde": return "tarde"
    return None
