# desktop/app_desktop.py
# -*- coding: utf-8 -*-

import os
import sys
import csv
from datetime import date, datetime
from calendar import monthrange
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ----------------------------------------------------------------------
# Tema (opcional)
# ----------------------------------------------------------------------
USE_BOOTSTRAP = True
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
except Exception:
    tb = None
    USE_BOOTSTRAP = False

if os.getenv("NO_BOOTSTRAP") == "1":
    USE_BOOTSTRAP = False
    tb = None

BOOTSTRAP_THEME = os.getenv("BOOTSTRAP_THEME", "flatly").strip() or "flatly"

# ----------------------------------------------------------------------
# tkcalendar (Calendar)
# ----------------------------------------------------------------------
from tkcalendar import Calendar as TKCalendar

# Patches de compatibilidade (mantidos conforme sua versão)
try:
    import ttkbootstrap.style as _tbs
    import tkcalendar.calendar_ as _tkcal
    from tkinter import ttk as _ttk

    def _mk_noop(name):
        def _noop(self, *args, **kwargs):
            return None
        return _noop

    _MISSING = [
        "create_date_frame_style",
        "create_date_entry_style",
        "create_date_label_style",
        "create_calendar_style",
    ]
    for n in _MISSING:
        if hasattr(_tbs, "StyleBuilderTTK") and not hasattr(_tbs.StyleBuilderTTK, n):
            setattr(_tbs.StyleBuilderTTK, n, _mk_noop(n))

    _orig_init = _tkcal.Calendar.__init__
    _orig_conf = _tkcal.Calendar.configure
    _orig_setitem = _tkcal.Calendar.__setitem__
    _FRAME_KEYS = {"style", "bootstyle", "padding", "takefocus", "cursor", "class"}

    def _safe_init(self, master=None, **kw):
        self._properties = {}
        return _orig_init(self, master, **kw)

    def _split_props(self, kwargs):
        known, unknown = {}, {}
        props = getattr(self, "_properties", {})
        for k, v in kwargs.items():
            if k in props and k not in _FRAME_KEYS:
                known[k] = v
            else:
                unknown[k] = v
        return known, unknown

    def _safe_conf(self, *args, **kwargs):
        if not kwargs and len(args) == 1 and isinstance(args[0], dict):
            kwargs = dict(args[0])
            args = ()
        if not hasattr(self, "_properties"):
            return _ttk.Frame.configure(self, **kwargs)
        known, unknown = _split_props(self, kwargs)
        if unknown:
            try:
                _ttk.Frame.configure(self, **unknown)
            except Exception:
                pass
        if known:
            return _orig_conf(self, **known)
        return None

    def _safe_setitem(self, key, value):
        props = getattr(self, "_properties", {})
        if (key not in props) or (key in _FRAME_KEYS):
            try:
                return _ttk.Frame.configure(self, **{key: value})
            except Exception:
                return
        return _orig_setitem(self, key, value)

    _tkcal.Calendar.__init__ = _safe_init
    _tkcal.Calendar.configure = _safe_conf
    _tkcal.Calendar.__setitem__ = _safe_setitem

except Exception:
    pass

# ----------------------------------------------------------------------
# Importa SUPABASE e funções de autenticação
# ----------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from database import get_usuario  # login via Supabase
from supabase_client import supabase  # cliente supabase

# caminho para recursos (ícones / logos)
def resource_path(*parts):
    candidates = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidates.append(os.path.join(base, *parts))
    candidates.append(os.path.join(os.path.dirname(__file__), *parts))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), *parts))
    candidates.append(os.path.join(os.getcwd(), *parts))
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(*parts)

# ======================================================================
# Helpers gerais
# ======================================================================

def parse_ymd_or_br(s: str | None) -> date | None:
    """
    Converte string para date.
    Aceita formatos:
      - YYYY-MM-DD
      - YYYY-MM-DDTHH:MM:SS (ISO com hora)
      - YYYY-MM-DD HH:MM:SS
      - DD/MM/YYYY
    Retorna date (sem tempo) ou None.
    """
    if not s:
        return None
    s = str(s).strip()
    fmts = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y")
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    # algumas APIs retornam iso com microsegundos: 2025-12-11T04:13:18.123456Z
    try:
        # tenta cortar após o 'T' e '.' se houver
        if "T" in s:
            s2 = s.split("T")[0]
            return datetime.strptime(s2, "%Y-%m-%d").date()
    except Exception:
        pass
    return None

def to_br(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if isinstance(d, (date, datetime)) else ""

def to_ymd(d: date | None) -> str:
    return d.strftime("%Y-%m-%d") if isinstance(d, (date, datetime)) else ""

# ======================================================================
# Estilos calendário
# ======================================================================

DP = {
    "font": ("Segoe UI", 10),
    "heading_font": ("Segoe UI Semibold", 10),
    "bg": "#ffffff",
    "fg": "#222222",
    "muted": "#6b7280",
    "border": "#D9DEE7",
    "header_bg": "#f8f9fa",
    "sel_bg": "#0d6efd",
    "sel_fg": "#ffffff",
    "other_bg": "#f5f5f5",
}

# ======================================================================
# DatePicker Moderno
# ======================================================================
# (Bloco mantido igual ao original — sem mudanças funcionais)
# Para economizar espaço neste chat, assumo que você mantém o mesmo DatePicker
# que já havia no arquivo original. Ele é reutilizado abaixo como DatePicker.
# Se quiser, posso colar o bloco inteiro aqui também.
# ----------------------------------------------------------------------

# ==== Aqui assume-se que DatePicker está definido ====
# Se no seu arquivo original o DatePicker tem outro nome, ajuste abaixo.

# ----------------------------------------------------------------------
# Login via Supabase
# ----------------------------------------------------------------------

class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Login - FCJA")
        self.resizable(False, False)
        self.transient(master)
        self.valid = False
        self._logo_img = None

        header_bg = "#0d6efd"
        header = tk.Frame(self, bg=header_bg)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        for p in (resource_path("assets", "logo.png"), resource_path("assets", "logo.gif")):
            try:
                if os.path.exists(p):
                    self._logo_img = tk.PhotoImage(file=p)
                    break
            except Exception:
                pass

        if self._logo_img:
            tk.Label(header, image=self._logo_img, bg=header_bg).grid(row=0, column=0, padx=12, pady=10)

        tk.Label(
            header, text="Fundação Casa de José Américo",
            bg=header_bg, fg="white", font=("Segoe UI Semibold", 10)
        ).grid(row=0, column=1, sticky="w", padx=(0, 12))

        frm = ttk.Frame(self, padding=16)
        frm.grid(row=1, column=0, sticky="nsew")

        ttk.Label(frm, text="Usuário").grid(row=0, column=0, sticky="w")
        self.e_user = ttk.Entry(frm, width=28)
        self.e_user.insert(0, "admin")
        self.e_user.grid(row=1, column=0, sticky="ew")

        ttk.Label(frm, text="Senha").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.e_pass = ttk.Entry(frm, width=28, show="*")
        self.e_pass.grid(row=3, column=0, sticky="ew")

        Btn = tb.Button if (USE_BOOTSTRAP and tb) else ttk.Button
        Btn(frm, text="Entrar", command=self.try_login,
            **({"bootstyle": "primary"} if (USE_BOOTSTRAP and tb) else {})
            ).grid(row=4, column=0, sticky="ew", pady=16)

        self.bind("<Return>", lambda e: self.try_login())

    def try_login(self):
        user = (self.e_user.get() or "").strip()
        pw = (self.e_pass.get() or "").strip()

        if not user or not pw:
            messagebox.showwarning("Login", "Informe usuário e senha.")
            return

        try:
            ok = get_usuario(user, pw)
            if ok:
                self.valid = True
                self.destroy()
            else:
                messagebox.showerror("Login", "Usuário ou senha inválidos.")
        except Exception as e:
            messagebox.showerror("Login", f"Erro no banco: {e!r}")

# ======================================================================
# Aplicação administrativa
# ======================================================================

class AdminApp(ttk.Frame):
    TABS = ("visitante","escola","ies","pesquisador")

    # Atualizei as colunas para incluir horario_chegada e duracao.
    # Substituí `tempo_estimado` por (horario_chegada, duracao).
    COLS = {
        "visitante": [
            ("id","ID",60),
            ("nome","Nome",180),
            ("genero","Gênero",80),
            ("email","E-mail",200),
            ("telefone","Telefone",120),
            ("endereco","Endereço",220),
            ("qtd_pessoas","Qtd",60),
            ("data","Data",100),
            ("turno","Turno",70),
            ("horario_chegada","Horário chegada",110),
            ("duracao","Duração",90),
            ("observacao","Observação",200),
        ],
        "escola": [
            ("id","ID",60),
            ("nome_escola","Nome da escola",240),
            ("representante","Representante",180),
            ("email","E-mail",200),
            ("telefone","Telefone",120),
            ("endereco","Endereço",220),
            ("num_alunos","Alunos",80),
            ("data","Data",100),
            ("turno","Turno",70),
            ("horario_chegada","Horário chegada",110),
            ("duracao","Duração",90),
            ("observacao","Observação",200),
        ],
        "ies": [
            ("id","ID",60),
            ("nome_ies","IES",240),
            ("representante","Representante",180),
            ("email","E-mail",200),
            ("telefone","Telefone",120),
            ("endereco","Endereço",220),
            ("num_alunos","Alunos",80),
            ("data","Data",100),
            ("turno","Turno",70),
            ("horario_chegada","Horário chegada",110),
            ("duracao","Duração",90),
            ("observacao","Observação",200),
        ],
        "pesquisador": [
            ("id","ID",60),
            ("nome","Nome",180),
            ("genero","Gênero",80),
            ("email","E-mail",200),
            ("telefone","Telefone",120),
            ("instituicao","Instituição",180),
            ("pesquisa","Pesquisa",220),
            ("data","Data",100),
            ("turno","Turno",70),
            ("horario_chegada","Horário chegada",110),
            ("duracao","Duração",90),
            ("observacao","Observação",200),
        ],
    }

    def __init__(self, master):
        super().__init__(master, padding=0)
        self.master = master

        self.master.title("Agendamentos FCJA — Admin")
        self.master.geometry("1200x650")

        self.var_texto = tk.StringVar()

        self._build_ui()
        # refresh inicial após UI pronta
        self.after(200, self.refresh_current)

    # ---------------- UI ---------------------
    def _build_ui(self):
        outer = ttk.Frame(self, padding=10)
        outer.grid(row=0, column=0, sticky="ew")
        self.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        card = ttk.Labelframe(outer, text="Filtros de busca", padding=10)
        card.grid(row=0, column=0, sticky="ew")

        ttk.Label(card, text="Nome/Texto").grid(row=0, column=0, sticky="w")
        e_txt = ttk.Entry(card, textvariable=self.var_texto, width=30)
        e_txt.grid(row=1, column=0, padx=5)

        # Período
        ttk.Label(card, text="Período").grid(row=0, column=1, sticky="w")
        wrap = ttk.Frame(card)
        wrap.grid(row=1, column=1)
        # DatePicker deve estar definido no seu código original
        # Caso não esteja, substitua por Entries padrão.
        try:
            self.dp_from = DatePicker(wrap, None, width=12)
            self.dp_to = DatePicker(wrap, None, width=12)
        except Exception:
            # fallback simples: entradas de texto com placeholder
            self.dp_from = ttk.Entry(wrap, width=12)
            self.dp_to = ttk.Entry(wrap, width=12)
            self.dp_from.insert(0, "")
            self.dp_to.insert(0, "")
        self.dp_from.grid(row=0, column=0, padx=5)
        self.dp_to.grid(row=0, column=1, padx=5)

        # Botões
        Btn = tb.Button if (USE_BOOTSTRAP and tb) else ttk.Button
        wrapb = ttk.Frame(card)
        wrapb.grid(row=1, column=2, padx=10)

        Btn(wrapb, text="Aplicar", command=self.apply_filters,
            **({"bootstyle":"primary"} if (USE_BOOTSTRAP and tb) else {})
            ).grid(row=0, column=0, padx=3)

        Btn(wrapb, text="Limpar", command=self.clear_filters,
            **({"bootstyle":"secondary-outline"} if (USE_BOOTSTRAP and tb) else {})
            ).grid(row=0, column=1, padx=3)

        Btn(wrapb, text="Atualizar", command=self.refresh_current,
            **({"bootstyle":"info"} if (USE_BOOTSTRAP and tb) else {})
            ).grid(row=0, column=2, padx=3)

        Btn(wrapb, text="Exportar CSV", command=self.export_csv,
            **({"bootstyle":"success-outline"} if (USE_BOOTSTRAP and tb) else {})
            ).grid(row=0, column=3, padx=6)

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.grid(row=1, column=0, sticky="nsew")

        self.tables = {}
        for tab in self.TABS:
            frame = ttk.Frame(self.nb, padding=8)
            self.nb.add(frame, text=tab.capitalize())
            cols = [c[0] for c in self.COLS[tab]]

            tree = ttk.Treeview(frame, columns=cols, show="headings")
            vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            for key, title, w in self.COLS[tab]:
                tree.heading(key, text=title)
                tree.column(key, width=w, anchor="w")

            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")

            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            self.tables[tab] = tree

        self.status = ttk.Label(self, anchor="w", padding=4)
        self.status.grid(row=2, column=0, sticky="ew")

        # bind para trocar aba
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_current())

    # ---------------- FILTROS ---------------------
    def clear_filters(self):
        self.var_texto.set("")
        try:
            if hasattr(self.dp_from, "set_date"):
                self.dp_from.set_date(None)
                self.dp_to.set_date(None)
            else:
                self.dp_from.delete(0, tk.END)
                self.dp_to.delete(0, tk.END)
        except Exception:
            pass
        self.refresh_current()

    def apply_filters(self):
        self.refresh_current()

    # ---------------- CONSULTA SUPABASE ---------------------
    def _query_tab(self, tab: str, texto: str, d1: date | None, d2: date | None):
        q = supabase.table(tab).select("*")

        if texto:
            p = f"%{texto}%"
            if tab == "visitante":
                q = q.or_(f"nome.ilike.{p},email.ilike.{p},telefone.ilike.{p},endereco.ilike.{p}")
            elif tab == "escola":
                q = q.or_(f"nome_escola.ilike.{p},representante.ilike.{p},email.ilike.{p},telefone.ilike.{p}")
            elif tab == "ies":
                q = q.or_(f"nome_ies.ilike.{p},representante.ilike.{p},email.ilike.{p},telefone.ilike.{p}")
            else:  # pesquisador
                q = q.or_(f"nome.ilike.{p},email.ilike.{p},telefone.ilike.{p},instituicao.ilike.{p},pesquisa.ilike.{p}")

        if d1:
            q = q.gte("data", d1.isoformat())
        if d2:
            q = q.lte("data", d2.isoformat())

        q = q.order("data", desc=True).order("id", desc=True).limit(1000)

        resp = q.execute()
        return resp.data or []

    # ---------------- ATUALIZAÇÃO ---------------------
    def current_tab(self):
        idx = self.nb.index(self.nb.select())
        return self.TABS[idx]

    def refresh_current(self):
        tab = self.current_tab()
        tree = self.tables[tab]
        tree.delete(*tree.get_children())

        texto = self.var_texto.get().strip()
        # obtem datas do DatePicker (ou fallback)
        try:
            if hasattr(self.dp_from, "get_date"):
                d1 = self.dp_from.get_date()
                d2 = self.dp_to.get_date()
            else:
                d1 = parse_ymd_or_br(self.dp_from.get()) if self.dp_from.get().strip() else None
                d2 = parse_ymd_or_br(self.dp_to.get()) if self.dp_to.get().strip() else None
        except Exception:
            d1 = d2 = None

        try:
            rows = self._query_tab(tab, texto, d1, d2)
            for r in rows:
                if "data" in r:
                    try:
                        parsed = parse_ymd_or_br(r["data"])
                        r["data"] = to_br(parsed) if parsed else (r.get("data") or "")
                    except Exception:
                        pass
                # garante que chaves existam (evita None)
                for key, _, _ in self.COLS[tab]:
                    if key not in r:
                        r[key] = ""
                values = [r.get(c[0], "") for c in self.COLS[tab]]
                tree.insert("", "end", values=values)
            self.status.config(text=f"{tab.capitalize()}: {len(rows)} registro(s)")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados:\n{e!r}")

    # ---------------- EXPORTAÇÃO ---------------------
    def export_csv(self):
        tab = self.current_tab()
        tree = self.tables[tab]
        items = tree.get_children()
        if not items:
            messagebox.showinfo("Exportar CSV", "Nada para exportar.")
            return

        fn = filedialog.asksaveasfilename(
            title="Salvar CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"{tab}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not fn:
            return

        # Cabeçalhos a partir das COLS (rótulos legíveis)
        headers = [t for _, t, _ in self.COLS[tab]]

        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(headers)
            for iid in items:
                w.writerow(tree.item(iid, "values"))

        messagebox.showinfo("Exportar CSV", f"Arquivo salvo:\n{fn}")

# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":

    if USE_BOOTSTRAP and tb:
        root = tb.Window(themename=BOOTSTRAP_THEME)
    else:
        root = tk.Tk()

    dlg = LoginDialog(root)
    root.wait_window(dlg)
    if not dlg.valid:
        root.destroy()
        sys.exit(0)

    app = AdminApp(root)
    root.mainloop()