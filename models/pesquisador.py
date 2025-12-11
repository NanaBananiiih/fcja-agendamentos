# models/pesquisador.py
from typing import Tuple, List, Dict, Any, Optional
from database import get_connection
from utils.validacoes import validar_email, validar_telefone, validar_data_pesquisa, normalizar_turno

def cadastrar_pesquisador(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insere agendamento de pesquisador. Retorna o registro inserido (dict) ou None.
    """
    if not validar_email(data.get('email','')): 
        raise ValueError('E-mail inválido')
    if not validar_telefone(data.get('telefone','')): 
        raise ValueError('Telefone inválido')
    if not validar_data_pesquisa(data.get('data','')): 
        raise ValueError('Data inválida (seg-sex)')
    t = normalizar_turno(data.get('turno',''))
    if not t:
        raise ValueError('Turno inválido')

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pesquisador
                  (nome, genero, email, telefone, instituicao, pesquisa, data, turno, tempo_estimado, observacao)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    data.get('nome'),
                    data.get('genero'),
                    data.get('email'),
                    data.get('telefone'),
                    data.get('instituicao'),
                    data.get('pesquisa'),
                    data.get('data'),
                    t,
                    data.get('tempo_estimado'),
                    data.get('observacao'),
                )
            )
            row = cur.fetchone()
            conn.commit()
            return row
    finally:
        conn.close()

def listar(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pesquisador ORDER BY id DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
            return rows or []
    finally:
        conn.close()
