import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import init_db, get_connection
from admin import relatorio_por_data, relatorio_por_turno, exportar_tudo_csv
init_db()
def autenticar(username, password):
    conn = get_connection(); cur = conn.cursor()
    cur.execute('SELECT id FROM usuarios WHERE username=? AND password=? AND ativo=1', (username, password))
    ok = cur.fetchone() is not None; conn.close(); return ok
class Login(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Login Administrativo'); self.geometry('400x220')
        frm = ttk.Frame(self, padding=16); frm.pack(expand=True, fill='both')
        ttk.Label(frm, text='Usuário').grid(row=0, column=0, sticky='w'); self.u = tk.StringVar(); ttk.Entry(frm, textvariable=self.u).grid(row=0,column=1)
        ttk.Label(frm, text='Senha').grid(row=1, column=0, sticky='w'); self.p = tk.StringVar(); ttk.Entry(frm, textvariable=self.p, show='*').grid(row=1,column=1)
        ttk.Button(frm, text='Entrar', command=self.try_login).grid(row=2, column=0, columnspan=2, pady=12)
    def try_login(self):
        if autenticar(self.u.get(), self.p.get()): self.destroy(); Admin().mainloop()
        else: messagebox.showerror('Erro','Usuário/senha inválidos')
class Admin(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('FCJA - Administração'); self.geometry('1000x600')
        toolbar = ttk.Frame(self); toolbar.pack(fill='x')
        ttk.Button(toolbar, text='Listar Visitantes', command=lambda: self.listar('visitante')).pack(side='left')
        ttk.Button(toolbar, text='Relatório (intervalo)', command=self.rel_intervalo).pack(side='left')
        ttk.Button(toolbar, text='Exportar tudo CSV', command=self.exportar_tudo).pack(side='left')
        ttk.Button(toolbar, text='Novo usuário', command=self.novo_usuario).pack(side='left')
        ttk.Button(toolbar, text='Sair', command=self.quit).pack(side='right')
        self.tree = ttk.Treeview(self, show='headings'); self.tree.pack(fill='both', expand=True)
    def listar(self, tabela):
        conn = get_connection(); cur = conn.cursor()
        rows = cur.execute(f'SELECT * FROM {tabela} ORDER BY id DESC LIMIT 200').fetchall()
        cols = [d[0] for d in cur.description]; conn.close()
        self.tree.delete(*self.tree.get_children()); self.tree['columns'] = cols
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=120)
        for r in rows: self.tree.insert('', 'end', values=r)
    def rel_intervalo(self):
        inicio = simpledialog.askstring('Inicio','Data inicial (YYYY-MM-DD):', parent=self)
        fim = simpledialog.askstring('Fim','Data final (YYYY-MM-DD):', parent=self)
        if not inicio or not fim: return
        resultados, path = relatorio_por_data(inicio, fim, exportar_csv=True)
        messagebox.showinfo('Relatório', '\n'.join(f'{t}: {q}' for t,q in resultados) + (f'\nCSV: {path}' if path else ''))
    def exportar_tudo(self):
        paths = exportar_tudo_csv(); messagebox.showinfo('Exportado', '\n'.join(paths))
    def novo_usuario(self):
        u = simpledialog.askstring('Usuário','Nome do usuário:', parent=self)
        p = simpledialog.askstring('Senha','Senha (texto puro):', parent=self, show='*')
        if not u or not p: return
        conn = get_connection(); cur = conn.cursor()
        try: cur.execute('INSERT INTO usuarios (username,password,ativo) VALUES (?,?,1)', (u,p)); conn.commit(); messagebox.showinfo('OK','Usuário criado')
        except Exception as e: messagebox.showerror('Erro', str(e))
        finally: conn.close()
if __name__ == '__main__':
    Login().mainloop()
