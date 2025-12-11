# models/ies.py
from utils.validacoes import (
    validar_email, validar_telefone, validar_data_visita, normalizar_turno
)

from database import insert_ies  # função que usa Supabase para inserir
from supabase_client import supabase  # para listagens

def cadastrar_ies(data):
    """
    Valida e cadastra um registro de IES usando Supabase.
    Lança ValueError em caso de validação.
    Retorna o registro criado (dict) em caso de sucesso.
    """
    if not validar_email(data.get('email','')):
        raise ValueError('E-mail inválido')
    if not validar_telefone(data.get('telefone','')):
        raise ValueError('Telefone inválido')
    if not validar_data_visita(data.get('data','')):
        raise ValueError('Data inválida (terça-dom)')
    t = normalizar_turno(data.get('turno',''))
    if not t:
        raise ValueError('Turno inválido')

    payload = {
        "nome_ies": data.get("nome_ies"),
        "representante": data.get("representante"),
        "email": data.get("email"),
        "telefone": data.get("telefone"),
        "endereco": data.get("endereco"),
        "num_alunos": int(data.get("num_alunos") or 0),
        "data": data.get("data"),  # use 'YYYY-MM-DD' preferencialmente
        "turno": t,
        "observacao": data.get("observacao"),
    }

    novo = insert_ies(payload)
    if not novo:
        raise RuntimeError("Falha ao inserir registro no Supabase.")
    return novo


def listar(limit=50):
    """
    Lista registros da tabela 'ies' usando Supabase.
    Retorna (cols, rows) onde cols = list de nomes de colunas e rows = lista de tuplas.
    """
    try:
        resp = (
            supabase.table("ies")
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
        # Em caso de erro, devolve listas vazias (não quebra o restante do app)
        print("Erro ao listar IES:", e)
        return [], []
