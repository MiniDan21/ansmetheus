#!/usr/bin/env python3
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Any, List, Optional

# ===== импорт Executor =====
from ans.executor import Executor

# Требуется PyYAML
try:
    import yaml
except ImportError:
    raise SystemExit("Требуется пакет PyYAML: pip install pyyaml")

# ------------------------------
# Модель состояния GUI
# ------------------------------

CONFIG_PATH = Path.home() / ".ansmetheus_gui.json"


class AppState:
    def __init__(self):
        self.inventory_files: List[str] = []
        self.recent_playbooks: List[str] = []
        self.inventory_data: Dict[str, Any] = {}
        self.groups: Dict[str, List[str]] = {}
        self.hosts: Dict[str, Dict[str, Any]] = {}

        self._load_config()

    def _load_config(self):
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                self.recent_playbooks = data.get("recent_playbooks", [])
                inv = data.get("inventory_files", [])
                if isinstance(inv, list):
                    self.inventory_files = inv
            except Exception:
                self.recent_playbooks = []
                self.inventory_files = []

    def _save_config(self):
        payload = {
            "recent_playbooks": self.recent_playbooks[:20],
            "inventory_files": self.inventory_files[:10],
        }
        CONFIG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_recent_playbook(self, path: str):
        p = str(Path(path).resolve())
        if p in self.recent_playbooks:
            self.recent_playbooks.remove(p)
        self.recent_playbooks.insert(0, p)
        self._save_config()

    def set_inventory_files(self, files: List[str]):
        norm = [str(Path(f).resolve()) for f in files]
        self.inventory_files = norm
        self._save_config()

    # ----- Парсинг inventory -----
    def load_inventory(self) -> None:
        self.inventory_data = {}
        self.groups = {}
        self.hosts = {}

        if not self.inventory_files:
            return

        merged: Dict[str, Any] = {}
        for path in self.inventory_files:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            merged = self._deep_merge(merged, data)

        if "all" not in merged:
            merged = {"all": {"children": merged}}

        self._parse_group("all", merged["all"])

    def _deep_merge(self, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        res = dict(a)
        for k, v in b.items():
            if k in res and isinstance(res[k], dict) and isinstance(v, dict):
                res[k] = self._deep_merge(res[k], v)
            else:
                res[k] = v
        return res

    def _parse_group(self, group_name: str, group_data: Dict[str, Any]):
        self.groups.setdefault(group_name, [])

        hosts_data = group_data.get("hosts", {}) or {}
        for host_name, params in hosts_data.items():
            params = params or {}
            existing = self.hosts.get(host_name, {})
            existing.update(params)
            self.hosts[host_name] = existing
            if host_name not in self.groups[group_name]:
                self.groups[group_name].append(host_name)

        children = group_data.get("children", {}) or {}
        for child_name, child_data in children.items():
            if child_data is None:
                self.groups.setdefault(child_name, [])
                for h in self.groups.get(child_name, []):
                    if h not in self.groups[group_name]:
                        self.groups[group_name].append(h)
            else:
                self._parse_group(child_name, child_data)
                for h in self.groups.get(child_name, []):
                    if h not in self.groups[group_name]:
                        self.groups[group_name].append(h)


# ------------------------------
# Базовый каркас страниц
# ------------------------------

class BasePage(ttk.Frame):
    def __init__(self, parent, controller: "App", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller

    def on_show(self):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ansmetheus — панель")
        self.geometry("900x600")
        self.minsize(800, 500)

        try:
            self.call("tk", "scaling", 1.2)
        except Exception:
            pass

        self.state = AppState()

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.pages: Dict[str, BasePage] = {}
        for PageCls in (HomePage, ServersPage, GroupsPage, RunPlaybookPage, MonitoringPage, SchedulePage):
            frame = PageCls(container, self)
            self.pages[PageCls.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.show_page("HomePage")

    def show_page(self, name: str):
        frame = self.pages[name]
        frame.tkraise()
        frame.on_show()

    def go_home(self): self.show_page("HomePage")
    def go_servers(self): self.show_page("ServersPage")
    def go_groups(self): self.show_page("GroupsPage")
    def go_run_playbook(self): self.show_page("RunPlaybookPage")
    def go_monitoring(self): self.show_page("MonitoringPage")
    def go_schedule(self): self.show_page("SchedulePage")


# ------------------------------
# Главная страница
# ------------------------------

class HomePage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        title = ttk.Label(self, text="Ansmetheus — стартовая страница", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=12, pady=(14, 8))
        ttk.Label(self, text="Выберите действие:").pack(anchor="w", padx=12, pady=(0, 10))

        btns = ttk.Frame(self)
        btns.pack(anchor="nw", fill="x", padx=12, pady=(0, 10))

        def add_btn(text, cmd):
            ttk.Button(btns, text=text, command=cmd).pack(fill="x", pady=4, padx=8)

        add_btn("Список серверов", controller.go_servers)
        add_btn("Список групп", controller.go_groups)
        add_btn("Запустить playbook (обзор или недавние)", controller.go_run_playbook)
        add_btn("Открыть Inventory файл (обзор)", self.open_inventory_file)
        add_btn("Мониторинг (пока не реализовано)", controller.go_monitoring)
        add_btn("Задать расписание (пока не реализовано)", controller.go_schedule)

        self.info = ttk.Label(self, text="", foreground="#666", wraplength=600, justify="left")
        self.info.pack(anchor="w", padx=12, pady=(12, 0))

    def on_show(self):
        inv = "\n".join(self.controller.state.inventory_files) or "Не выбран"
        self.info.config(text=f"Текущий inventory:\n{inv}")

    def open_inventory_file(self):
        files = filedialog.askopenfilenames(
            title="Выберите inventory YAML",
            filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")]
        )
        if not files: return
        self.controller.state.set_inventory_files(list(files))
        try:
            self.controller.state.load_inventory()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить inventory:\n{e}")
            return
        messagebox.showinfo("Готово", "Inventory успешно загружен.")
        self.on_show()


# ------------------------------
# Список серверов
# ------------------------------

class ServersPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)
        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)
        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Список серверов", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        self.tree = ttk.Treeview(self, columns=("ip", "username"), show="headings", height=18)
        self.tree.heading("ip", text="IP / Host")
        self.tree.heading("username", text="Username")
        self.tree.column("ip", width=300)
        self.tree.column("username", width=200)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

    def on_show(self):
        self.tree.delete(*self.tree.get_children())
        st = self.controller.state
        if not st.hosts and st.inventory_files:
            try:
                st.load_inventory()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить inventory:\n{e}")
                return
        for host_name, params in sorted(st.hosts.items()):
            ip = params.get("ip", host_name)
            username = params.get("username", "")
            self.tree.insert("", "end", values=(f"{host_name} ({ip})", username))


# ------------------------------
# Список групп
# ------------------------------

class GroupsPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)
        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)
        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Список групп", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        self.tree = ttk.Treeview(self, columns=("members",), show="headings", height=18)
        self.tree.heading("members", text="Хосты")
        self.tree.column("members", width=700)
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

    def on_show(self):
        self.tree.delete(*self.tree.get_children())
        st = self.controller.state
        if not st.groups and st.inventory_files:
            try:
                st.load_inventory()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить inventory:\n{e}")
                return
        for grp, members in sorted(st.groups.items()):
            mem = ", ".join(members) if members else "(пусто)"
            self.tree.insert("", "end", values=(f"{grp}: {mem}",))


# ------------------------------
# Запуск Playbook (реальный)
# ------------------------------


class RunPlaybookPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)
        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)
        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Запустить playbook", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        # --- выбор группы или хоста ---
        ttk.Label(self, text="Выберите хост или группу:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.host_var = tk.StringVar()
        self.host_combo = ttk.Combobox(self, textvariable=self.host_var, state="readonly")
        self.host_combo.pack(fill="x", padx=10, pady=(0, 8))

        # --- sudo ---
        self.sudo_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Выполнить с sudo", variable=self.sudo_var).pack(anchor="w", padx=10, pady=(0, 8))

        # --- playbook ---
        ttk.Label(self, text="Playbook файлы:").pack(anchor="w", padx=10)
        self.pb_list = tk.Listbox(self, height=3)
        self.pb_list.pack(fill="x", padx=10)
        ttk.Button(self, text="Добавить playbook...", command=self.add_playbook).pack(anchor="e", padx=10, pady=(4, 8))

        # --- кнопка запуска ---
        ttk.Button(self, text="▶ Запустить playbook", command=self.run_playbook).pack(anchor="center", pady=(6, 10))

        # --- лог выполнения ---
        self.log = tk.Text(self, height=14, wrap="word", bg="#f9f9f9", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, padx=10, pady=(6, 10))

    def on_show(self):
        """Обновляем список групп/хостов из inventory"""
        st = self.controller.state
        if not st.groups and st.inventory_files:
            try:
                st.load_inventory()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить inventory:\n{e}")
                return

        all_options = sorted(set(list(st.groups.keys()) + list(st.hosts.keys())))
        self.host_combo["values"] = all_options
        if all_options:
            self.host_combo.current(0)

    def add_playbook(self):
        files = filedialog.askopenfilenames(title="Выберите playbook", filetypes=[("YAML", "*.yml *.yaml")])
        for f in files:
            self.pb_list.insert(tk.END, f)

    def run_playbook(self):
        host_group = self.host_var.get().strip()
        inventory_files = self.controller.state.inventory_files
        playbook_files = list(self.pb_list.get(0, tk.END))
        sudo = self.sudo_var.get()

        if not host_group or not inventory_files or not playbook_files:
            messagebox.showerror("Ошибка", "Выберите хост/группу и хотя бы один playbook.")
            return

        self._append_log(f"\n▶ Запуск playbook для [{host_group}]...\n")
        try:
            executor = Executor(host_group, inventory_files)
            executor.execute_playbook(playbook_files)
            self._append_log("✅ Завершено успешно.\n")
        except Exception as e:
            self._append_log(f"❌ Ошибка: {e}\n")

    def _append_log(self, text):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)


# ------------------------------
# Мониторинг (заглушка)
# ------------------------------

class MonitoringPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)
        ttk.Button(self, text="← Назад", command=self.controller.go_home).pack(anchor="w", padx=10, pady=8)
        ttk.Label(self, text="Мониторинг (пока не реализовано)", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(8, 4))


# ------------------------------
# Расписание (заглушка)
# ------------------------------

class SchedulePage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)
        ttk.Button(self, text="← Назад", command=self.controller.go_home).pack(anchor="w", padx=10, pady=8)
        ttk.Label(self, text="Задать расписание (пока не реализовано)", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(8, 4))


# ------------------------------
# Запуск GUI
# ------------------------------

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
