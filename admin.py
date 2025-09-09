import os, csv
from database import get_connection
REL_DIR = os.path.join(os.path.dirname(__file__), 'relatorios')
def relatorio_por_data(inicio, fim, exportar_csv=False):
    conn = get_connection(); cur = conn.cursor()
    tabelas = ['visitante','escola','ies','pesquisador']; resultados=[]
    for t in tabelas:
        total = cur.execute(f"SELECT COUNT(*) FROM {t} WHERE date(data) BETWEEN date(?) AND date(?)", (inicio, fim)).fetchone()[0]
        resultados.append((t,total))
    conn.close(); path=None
    if exportar_csv:
        os.makedirs(REL_DIR, exist_ok=True)
        path = os.path.join(REL_DIR, f'relatorio_intervalo_{inicio}_a_{fim}.csv')
        with open(path,'w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['tabela','total']); w.writerows(resultados)
    return resultados, path
def relatorio_por_turno(data, exportar_csv=False):
    conn = get_connection(); cur = conn.cursor(); tabelas=['visitante','escola','ies','pesquisador']; resultados=[]
    for t in tabelas:
        manha = cur.execute(f"SELECT COUNT(*) FROM {t} WHERE date(data)=date(?) AND turno='manhã'", (data,)).fetchone()[0]
        tarde = cur.execute(f"SELECT COUNT(*) FROM {t} WHERE date(data)=date(?) AND turno='tarde'", (data,)).fetchone()[0]
        resultados.append((t,manha,tarde))
    conn.close(); path=None
    if exportar_csv:
        os.makedirs(REL_DIR, exist_ok=True)
        path = os.path.join(REL_DIR, f'relatorio_turno_{data}.csv')
        with open(path,'w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['tabela','manha','tarde']); w.writerows(resultados)
    return resultados, path
def exportar_tudo_csv():
    conn = get_connection(); cur = conn.cursor(); os.makedirs(REL_DIR, exist_ok=True); paths=[]
    for t in ['visitante','escola','ies','pesquisador']:
        rows = cur.execute(f'SELECT * FROM {t} ORDER BY id DESC').fetchall()
        cols = [d[0] for d in cur.description]
        path = os.path.join(REL_DIR, f'{t}_completo.csv')
        with open(path,'w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(cols); w.writerows(rows)
        paths.append(path)
    conn.close(); return paths
