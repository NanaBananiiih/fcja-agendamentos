from utils.validacoes import (
    validar_email, validar_telefone,
    validar_data_visita, normalizar_turno
)

from database import insert_escola   # função que usa Supabase
from supabase_client import supabase  # cliente supabase


def cadastrar_escola(data):
    # --- validações ---
    if not validar_email(data.get('email','')):
        raise ValueError('E-mail inválido')

    if not validar_telefone(data.get('telefone','')):
        raise ValueError('Telefone inválido')

    if not validar_data_visita(data.get('data','')):
        raise ValueError('Data inválida (terça-dom)')

    turno = normalizar_turno(data.get('turno',''))
    if not turno:
        raise ValueError('Turno inválido')

    # --- monta payload para supabase ---
    payload = {
        "nome_escola": data.get("nome_escola"),
        "representante": data.get("representante"),
        "email": data.get("email"),
        "telefone": data.get("telefone"),
        "endereco": data.get("endereco"),
        "num_alunos": int(data.get("num_alunos") or 0),
        "data": data.get("data"),  # Supabase aceita 'YYYY-MM-DD'
        "turno": turno,
        "observacao": data.get("observacao"),
    }

    novo = insert_escola(payload)
    if not novo:
        raise RuntimeError("Falha ao inserir registro no Supabase.")

    return novo   # retorna o registro recém-criado


def listar(limit=50):
    """Lista registros de 'escola' usando Supabase"""
    try:
        resp = (
            supabase.table("escola")
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

        # transforma em lista de tuplas para manter compatibilidade antiga
        rows = [tuple(item[col] for col in cols) for item in dados]

        return cols, rows

    except Exception as e:
        print("Erro ao listar escolas:", e)
        return [], []
