# models/ies.py
from typing import Tuple, List, Dict, Any, Optional
from database import get_connection
from utils.validacoes import validar_email, validar_telefone, validar_data_visita, normalizar_turno

def cadastrar_ies(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insere agendamento do tipo IES. Retorna o registro inserido (dict) ou None.
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

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ies
                  (nome_ies, representante, email, telefone, endereco, num_alunos, data, turno, observacao)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    data.get('nome_ies'),
                    data.get('representante'),
                    data.get('email'),
                    data.get('telefone'),
                    data.get('endereco'),
                    int(data.get('num_alunos') or 0),
                    data.get('data'),
                    t,
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
            cur.execute("SELECT * FROM ies ORDER BY id DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
            return rows or []
    finally:
        conn.close()
