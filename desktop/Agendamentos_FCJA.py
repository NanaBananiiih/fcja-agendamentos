# -*- coding: utf-8 -*-
import os
import sys
import csv
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import ttkbootstrap as tb
from ttkbootstrap.constants import *

# --------------------------------------------------
# Caminho raiz
# --------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from supabase_client import supabase
from database import get_usuario

# --------------------------------------------------
# Helpers de data
# --------------------------------------------------
def br_to_iso(s):
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return None

def iso_to_br(s):
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return ""

# --------------------------------------------------
# Tooltip para Treeview
# --------------------------------------------------
class CellTooltip:
    def __init__(self, widget):
        self.widget = widget
        self.tip = None
        self.text = ""

        widget.bind("<Motion>", self.on_motion)
        widget.bind("<Leave>", self.hide)

    def on_motion(self, event):
        row_id = self.widget.identify_row(event.y)
        col_id = self.widget.identify_column(event.x)

        if not row_id or not col_id:
            self.hide()
            return

        col_index = int(col_id.replace("#", "")) - 1
        values = self.widget.item(row_id, "values")

        if col_index >= len(values):
            self.hide()
            return

        text = str(values[col_index])
        if not text or text == "None":
            self.hide()
            return

        if text != self.text:
            self.text = text
            self.show(event.x_root + 15, event.y_root + 10, text)

    def show(self, x, y, text):
        self.hide()
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tip,
            text=text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padding=6,
            wraplength=500
        )
        label.pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
            self.text = ""

# --------------------------------------------------
# Login
# --------------------------------------------------
class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Login - FCJA")
        self.resizable(False, False)
        self.valid = False

        frame = ttk.Frame(self, padding=20)
        frame.pack()

        try:
            logo = tk.PhotoImage(file=os.path.join(ROOT, "assets", "logo.png"))
            lbl = ttk.Label(frame, image=logo)
            lbl.image = logo
            lbl.pack(pady=5)
        except Exception:
            pass

        ttk.Label(
            frame,
            text="Fundação Casa de José Américo",
            font=("Segoe UI Semibold", 12)
        ).pack(pady=10)

        ttk.Label(frame, text="Usuário").pack(anchor="w")
        self.e_user = ttk.Entry(frame)
        self.e_user.insert(0, "admin")
        self.e_user.pack(fill="x")

        ttk.Label(frame, text="Senha").pack(anchor="w", pady=(10, 0))
        self.e_pass = ttk.Entry(frame, show="*")
        self.e_pass.pack(fill="x")

        ttk.Button(
            frame,
            text="Entrar",
            bootstyle=PRIMARY,
            command=self.login
        ).pack(fill="x", pady=15)

    def login(self):
        if get_usuario(self.e_user.get(), self.e_pass.get()):
            self.valid = True
            self.destroy()
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos")

# --------------------------------------------------
# App principal
# --------------------------------------------------
class AdminApp(ttk.Frame):

    TABS = ("visitante", "escola", "ies", "pesquisador")

    COLS = {
        "visitante": [
            ("id","ID"), ("nome","Nome"), ("email","E-mail"),
            ("telefone","Telefone"), ("qtd_pessoas","Qtd pessoas"),
            ("data","Data"), ("turno","Turno"),
            ("horario_chegada","Horário chegada"),
            ("duracao","Duração"), ("observacao","Observação"),
        ],
        "escola": [
            ("id","ID"), ("nome_escola","Nome escola"),
            ("representante","Representante"), ("email","E-mail"),
            ("telefone","Telefone"), ("num_alunos","Alunos"),
            ("data","Data"), ("turno","Turno"),
            ("horario_chegada","Horário chegada"),
            ("duracao","Duração"), ("observacao","Observação"),
        ],
        "ies": [
            ("id","ID"), ("nome_ies","IES"),
            ("representante","Representante"), ("email","E-mail"),
            ("telefone","Telefone"), ("num_alunos","Alunos"),
            ("data","Data"), ("turno","Turno"),
            ("horario_chegada","Horário chegada"),
            ("duracao","Duração"), ("observacao","Observação"),
        ],
        "pesquisador": [
            ("id","ID"), ("nome","Nome"), ("email","E-mail"),
            ("telefone","Telefone"), ("instituicao","Instituição"),
            ("pesquisa","Pesquisa"), ("data","Data"),
            ("turno","Turno"), ("horario_chegada","Horário chegada"),
            ("duracao","Duração"), ("observacao","Observação"),
        ],
    }

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.search_text = tk.StringVar()
        self.date_from = tk.StringVar()
        self.date_to = tk.StringVar()

        self.build_filters()
        self.build_tabs()
        self.refresh()

    # ----------------- filtros -----------------
    def build_filters(self):
        box = ttk.Labelframe(self, text="Filtros", padding=10)
        box.pack(fill="x", padx=10, pady=5)

        ttk.Label(box, text="Buscar").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.search_text, width=30)\
            .grid(row=1, column=0, padx=5)

        ttk.Label(box, text="Data inicial (DD/MM/AAAA)").grid(row=0, column=1)
        ttk.Entry(box, textvariable=self.date_from, width=14)\
            .grid(row=1, column=1, padx=5)

        ttk.Label(box, text="Data final (DD/MM/AAAA)").grid(row=0, column=2)
        ttk.Entry(box, textvariable=self.date_to, width=14)\
            .grid(row=1, column=2, padx=5)

        ttk.Button(box, text="Aplicar", bootstyle=PRIMARY,
                   command=self.refresh).grid(row=1, column=3, padx=5)

        ttk.Button(box, text="Limpar", bootstyle=SECONDARY,
                   command=self.clear).grid(row=1, column=4, padx=5)

        ttk.Button(box, text="Atualizar", bootstyle=INFO,
                   command=self.refresh).grid(row=1, column=5, padx=5)

        ttk.Button(box, text="Exportar CSV", bootstyle=SUCCESS,
                   command=self.export_csv).grid(row=1, column=6, padx=5)

    # ----------------- abas -----------------
    def build_tabs(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=5)

        self.tables = {}

        for tab in self.TABS:
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=tab.capitalize())

            cols = [c[0] for c in self.COLS[tab]]

            yscroll = ttk.Scrollbar(frame, orient="vertical")
            xscroll = ttk.Scrollbar(frame, orient="horizontal")

            tree = ttk.Treeview(
                frame,
                columns=cols,
                show="headings",
                yscrollcommand=yscroll.set,
                xscrollcommand=xscroll.set
            )

            yscroll.config(command=tree.yview)
            xscroll.config(command=tree.xview)

            tree.grid(row=0, column=0, sticky="nsew")
            yscroll.grid(row=0, column=1, sticky="ns")
            xscroll.grid(row=1, column=0, sticky="ew")

            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            for key, title in self.COLS[tab]:
                tree.heading(key, text=title)
                if key in ("observacao", "nome", "nome_escola", "nome_ies", "pesquisa"):
                    tree.column(key, width=400, stretch=False)
                else:
                    tree.column(key, width=140, stretch=False)

            CellTooltip(tree)  # 🔥 TOOLTIP AQUI

            self.tables[tab] = tree

        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh())

    # ----------------- dados -----------------
    def refresh(self):
        tab = self.TABS[self.nb.index(self.nb.select())]
        tree = self.tables[tab]
        tree.delete(*tree.get_children())

        q = supabase.table(tab).select("*")

        if self.search_text.get().strip():
            txt = self.search_text.get().strip()
            field = self.COLS[tab][1][0]
            q = q.eq(field, txt)

        d1 = br_to_iso(self.date_from.get())
        d2 = br_to_iso(self.date_to.get())

        if d1 and d2:
            q = q.gte("data", d1).lte("data", d2)
        elif d1:
            q = q.eq("data", d1)
        elif d2:
            q = q.eq("data", d2)

        rows = q.order("data", desc=True).execute().data or []

        for r in rows:
            r["data"] = iso_to_br(r.get("data"))
            tree.insert("", "end",
                        values=[r.get(c[0], "") for c in self.COLS[tab]])

    def clear(self):
        self.search_text.set("")
        self.date_from.set("")
        self.date_to.set("")
        self.refresh()

    # ----------------- CSV -----------------
    def export_csv(self):
        tab = self.TABS[self.nb.index(self.nb.select())]
        tree = self.tables[tab]
        items = tree.get_children()

        if not items:
            messagebox.showinfo("CSV", "Sem dados para exportar")
            return

        path = os.path.join(
            os.getcwd(),
            f"{tab}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow([c[1] for c in self.COLS[tab]])
            for i in items:
                w.writerow(tree.item(i, "values"))

        os.startfile(path)

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    root.geometry("1200x700")
    root.minsize(1000, 600)

    dlg = LoginDialog(root)
    root.wait_window(dlg)

    if not dlg.valid:
        root.destroy()
        sys.exit()

    AdminApp(root)
    root.mainloop()