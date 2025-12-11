# models/visitante.py
from typing import Tuple, List, Dict, Any, Optional
from database import get_connection
from utils.validacoes import validar_email, validar_telefone, validar_data_visita, normalizar_turno

def cadastrar_visitante(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insere um visitante. Retorna o registro inserido (dict) ou None em caso de erro.
    Espera data['data'] como 'YYYY-MM-DD' ou objeto date; normaliza turno com normalizar_turno().
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
                INSERT INTO visitante
                  (nome, genero, email, telefone, endereco, qtd_pessoas, data, turno, tempo_estimado, observacao)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    data.get('nome'),
                    data.get('genero'),
                    data.get('email'),
                    data.get('telefone'),
                    data.get('endereco'),
                    int(data.get('qtd_pessoas') or 1),
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
    """Retorna lista de registros (lista de dicts) da tabela visitante."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM visitante ORDER BY id DESC LIMIT %s", (limit,))
            rows = cur.fetchall()
            return rows or []
    finally:
        conn.close()
