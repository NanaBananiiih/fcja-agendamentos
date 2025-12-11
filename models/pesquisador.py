# models/pesquisador.py

from utils.validacoes import (
    validar_email, validar_telefone,
    validar_data_pesquisa, normalizar_turno
)

from database import insert_pesquisador  # função que usa Supabase para inserir
from supabase_client import supabase     # cliente Supabase


def cadastrar_pesquisador(data):
    """
    Valida e cadastra um pesquisador usando Supabase.
    Retorna o registro criado ou lança ValueError/RuntimeError.
    """
    if not validar_email(data.get('email', '')):
        raise ValueError('E-mail inválido')

    if not validar_telefone(data.get('telefone', '')):
        raise ValueError('Telefone inválido')

    if not validar_data_pesquisa(data.get('data', '')):
        raise ValueError('Data inválida (seg-sex)')

    turno = normalizar_turno(data.get('turno', ''))
    if not turno:
        raise ValueError('Turno inválido')

    payload = {
        "nome": data.get("nome"),
        "genero": data.get("genero"),
        "email": data.get("email"),
        "telefone": data.get("telefone"),
        "instituicao": data.get("instituicao"),
        "pesquisa": data.get("pesquisa"),
        "data": data.get("data"),  # formato 'YYYY-MM-DD' ou válido para Supabase
        "turno": turno,
        "tempo_estimado": data.get("tempo_estimado"),
        "observacao": data.get("observacao"),
    }

    novo = insert_pesquisador(payload)
    if not novo:
        raise RuntimeError("Falha ao inserir registro no Supabase.")

    return novo


def listar(limit=50):
    """
    Lista registros de 'pesquisador' usando Supabase.
    Retorna (cols, rows) para manter compatibilidade com o app desktop.
    """
    try:
        resp = (
            supabase.table("pesquisador")
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

        # retorna lista de tuplas (compatível com o formato antigo do desktop)
        rows = [tuple(item.get(c) for c in cols) for item in dados]

        return cols, rows

    except Exception as e:
        print("Erro ao listar pesquisadores:", e)
        return [], []
