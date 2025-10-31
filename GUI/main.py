#!/usr/bin/env python3
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Any, List, Optional

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
                # игнорируем повреждённый конфиг
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

    # ----- Парсинг inventory (аналог Ansible YAML) -----
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
            # ленивое мердж-объединение
            merged = self._deep_merge(merged, data)

        # auto-wrap в all, если нет
        if "all" not in merged:
            merged = {"all": {"children": merged}}

        # Рекурсивный разбор
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
            # Обновляем/создаём хост
            existing = self.hosts.get(host_name, {})
            existing.update(params)
            self.hosts[host_name] = existing
            if host_name not in self.groups[group_name]:
                self.groups[group_name].append(host_name)

        children = group_data.get("children", {}) or {}
        for child_name, child_data in children.items():
            if child_data is None:
                # пустой child — просто связь
                self.groups.setdefault(child_name, [])
                # наследуем хосты
                for h in self.groups.get(child_name, []):
                    if h not in self.groups[group_name]:
                        self.groups[group_name].append(h)
            else:
                self._parse_group(child_name, child_data)
                # после разбора дочерней — подмешиваем хосты
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
        """Хук: вызывается при показе страницы."""
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ansmetheus — панель")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Тема
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

    # Навигация
    def go_home(self):
        self.show_page("HomePage")

    def go_servers(self):
        self.show_page("ServersPage")

    def go_groups(self):
        self.show_page("GroupsPage")

    def go_run_playbook(self):
        self.show_page("RunPlaybookPage")

    def go_monitoring(self):
        self.show_page("MonitoringPage")

    def go_schedule(self):
        self.show_page("SchedulePage")


# ------------------------------
# Главная страница
# ------------------------------

class HomePage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        padx = 12
        pady = 6

        title = ttk.Label(
            self,
            text="Ansmetheus — стартовая страница",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(anchor="w", padx=padx, pady=(14, 8))

        desc = ttk.Label(self, text="Выберите действие:")
        desc.pack(anchor="w", padx=padx, pady=(0, 10))

        # Контейнер для кнопок
        btns = ttk.Frame(self)
        btns.pack(anchor="nw", fill="x", padx=padx, pady=(0, 10))

        def add_btn(text, cmd):
            short_text = text.replace("(обзор или недавние)", "(обзор)")
            b = ttk.Button(btns, text=short_text, command=cmd)
            b.pack(fill="x", pady=4, padx=8)

        add_btn("Список серверов", controller.go_servers)
        add_btn("Список групп", controller.go_groups)
        add_btn("Запустить playbook (обзор или недавние)", controller.go_run_playbook)
        add_btn("Открыть Inventory файл (обзор)", self.open_inventory_file)
        add_btn("Мониторинг (пока не реализовано)", controller.go_monitoring)
        add_btn("Задать расписание (пока не реализовано)", controller.go_schedule)

        # Информационный лейбл
        self.info = ttk.Label(self, text="", foreground="#666", wraplength=600, justify="left")
        self.info.pack(anchor="w", padx=padx, pady=(12, 0))


    def on_show(self):
        inv = "\n".join(self.controller.state.inventory_files) or "Не выбран"
        self.info.config(text=f"Текущий inventory:\n{inv}")

    def open_inventory_file(self):
        files = filedialog.askopenfilenames(
            title="Выберите inventory YAML",
            filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")]
        )
        if not files:
            return
        self.controller.state.set_inventory_files(list(files))
        try:
            self.controller.state.load_inventory()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить inventory:\n{e}")
            return
        messagebox.showinfo("Готово", "Inventory успешно загружен.")
        self.on_show()


# ------------------------------
# Страница: Список серверов
# ------------------------------

class ServersPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)

        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Список серверов", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(body, columns=("ip", "username"), show="headings", height=18)
        self.tree.heading("ip", text="IP / Host")
        self.tree.heading("username", text="Username")
        self.tree.column("ip", width=300)
        self.tree.column("username", width=200)
        self.tree.pack(fill="both", expand=True, side="left")

        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

    def on_show(self):
        self.tree.delete(*self.tree.get_children())
        st = self.controller.state
        # Убедимся, что inventory загружен
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
# Страница: Список групп
# ------------------------------

class GroupsPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)

        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Список групп", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(body, columns=("members",), show="headings", height=18)
        self.tree.heading("members", text="Хосты")
        self.tree.column("members", width=700)
        self.tree.pack(fill="both", expand=True, side="left")

        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)

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
            if not members:
                mem = "(пусто)"
            else:
                mem = ", ".join(members)
            self.tree.insert("", "end", values=(f"{grp}: {mem}",))


# ------------------------------
# Страница: Запустить playbook (обзор/недавние)
# ------------------------------

class RunPlaybookPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)

        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Запустить playbook", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Недавние playbook:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.recent_list = tk.Listbox(left, height=16)
        self.recent_list.pack(fill="both", expand=True)

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=8)
        ttk.Button(btns, text="Выбрать файл...", command=self.choose_playbook).pack(side="left")
        ttk.Button(btns, text="Запомнить выбранный", command=self.remember_selected).pack(side="left", padx=6)

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        ttk.Label(right, text="Информация:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.info = tk.Text(right, height=20)
        self.info.pack(fill="both", expand=True)

        runbar = ttk.Frame(self)
        runbar.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(runbar, text="Имитация запуска (логика запуска не реализована)", command=self.simulate_run).pack(side="left")

    def on_show(self):
        self.recent_list.delete(0, "end")
        for p in self.controller.state.recent_playbooks:
            self.recent_list.insert("end", p)

    def choose_playbook(self):
        files = filedialog.askopenfilenames(
            title="Выберите playbook YAML",
            filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")]
        )
        if not files:
            return
        for f in files:
            self.controller.state.add_recent_playbook(f)
        self.on_show()
        self.info_delete_set(f"Добавлено в недавние:\n" + "\n".join(files))

    def remember_selected(self):
        sel = self.recent_list.curselection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите playbook из списка.")
            return
        path = self.recent_list.get(sel[0])
        self.controller.state.add_recent_playbook(path)
        self.info_delete_set(f"Закреплён playbook:\n{path}")

    def simulate_run(self):
        sel = self.recent_list.curselection()
        if not sel:
            messagebox.showinfo("Запуск", "Выберите playbook из списка.")
            return
        path = self.recent_list.get(sel[0])
        inv = self.controller.state.inventory_files or ["<не выбран>"]
        self.info_delete_set(
            "Имитация запуска:\n"
            f"  Inventory: {inv}\n"
            f"  Playbook:  {path}\n\n"
            "(Тут должна быть интеграция с Executor/Playbook. Пока только UI.)"
        )

    def info_delete_set(self, text: str):
        self.info.delete("1.0", "end")
        self.info.insert("1.0", text)


# ------------------------------
# Страница: Мониторинг (заглушка)
# ------------------------------

class MonitoringPage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)

        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Мониторинг (пока не реализовано)", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        lbl = ttk.Label(self, text="Здесь появится мониторинг состояния хостов/тасков.")
        lbl.pack(anchor="w", padx=8, pady=8)


# ------------------------------
# Страница: Расписание (заглушка)
# ------------------------------

class SchedulePage(BasePage):
    def __init__(self, parent, controller: App):
        super().__init__(parent, controller)

        header = ttk.Frame(self)
        header.pack(fill="x", pady=8, padx=8)

        ttk.Button(header, text="← Назад", command=self.controller.go_home).pack(side="left")
        ttk.Label(header, text="Задать расписание (пока не реализовано)", font=("Segoe UI", 14, "bold")).pack(side="left", padx=12)

        lbl = ttk.Label(self, text="Тут будет настройка cron/заданий для запуска playbook’ов.")
        lbl.pack(anchor="w", padx=8, pady=8)


# ------------------------------
# Запуск
# ------------------------------

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
