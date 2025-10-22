from ans.executor.bridge import Bridge
from ans.executor.initialization import Environment
from ans.playbook.task import Task


# создаём соединение
bridge = Bridge(ip_address="127.0.0.1")

# создаём окружение
env = Environment(bridge)
env.init()

# пример задач
tasks = [
    Task(name="Ping host", module_name="ping", args={"host": "127.0.0.1"}),
    Task(name="Install curl", module_name="apt", args={"name": "curl"}),
    Task(name="Run shell", module_name="shell", args={"cmd": "echo Hello"}),
    Task(name="Debug output", module_name="debug", args={"msg": "Everything OK!"}),
]

# выполняем все задачи
for t in tasks:
    t.run(bridge, env)

env.destroy()
