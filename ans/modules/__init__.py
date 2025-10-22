import os

# Список всех модулей
registry = []
key_files = ["__init__.py", "_base_module.py"]
for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith(".py") and file not in key_files:
        registry.append(os.path.splitext(os.path.basename(file))[0])
