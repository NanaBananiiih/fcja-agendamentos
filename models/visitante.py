# models/visitante.py

from utils.validacoes import (
    validar_email, validar_telefone,
    validar_data_visita, normalizar_turno
)

from database import insert_visitante  # função que usa Supabase para inserir
from supabase_client import supabase     # cliente Supabase


def cadastrar_visitante(data):
    """
    Valida e cadastra um visitante usando Supabase.
    Retorna o registro criado (dict) ou lança ValueError/RuntimeError.
    """
    if not validar_email(data.get('email', '')):
        raise ValueError('E-mail inválido')

    if not validar_telefone(data.get('telefone', '')):
        raise ValueError('Telefone inválido')

    if not validar_data_visita(data.get('data', '')):
        raise ValueError('Data inválida (terça-dom)')

    turno = normalizar_turno(data.get('turno', ''))
    if not turno:
        raise ValueError('Turno inválido')

    payload = {
        "nome": data.get("nome"),
        "genero": data.get("genero"),
        "email": data.get("email"),
        "telefone": data.get("telefone"),
        "endereco": data.get("endereco"),
        "qtd_pessoas": int(data.get("qtd_pessoas") or 1),
        "data": data.get("data"),  # formato 'YYYY-MM-DD' preferencial
        "turno": turno,
        "tempo_estimado": data.get("tempo_estimado"),
        "observacao": data.get("observacao"),
    }

    novo = insert_visitante(payload)
    if not novo:
        raise RuntimeError("Falha ao inserir registro no Supabase.")
    return novo


def listar(limit=50):
    """
    Lista registros de 'visitante' usando Supabase.
    Retorna (cols, rows) onde cols é lista de nomes de colunas e rows é lista de tuplas.
    """
    try:
        resp = (
            supabase.table("visitante")
            .select("*")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        dados = resp.data or []
        if dados:
            cols = list(dados[0].keys())
        else:
            cols = []
        rows = [tuple(item.get(c) for c in cols) for item in dados]
        return cols, rows
    except Exception as e:
        print("Erro ao listar visitantes:", e)
        return [], []
