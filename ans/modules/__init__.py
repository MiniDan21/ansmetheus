import os


key_files = ["__init__.py", "_base_module.py"]

# Список всех модулей
EXISTING_MODULES = [
    os.path.splitext(os.path.basename(file))[0]
    for file in os.listdir(os.path.dirname(__file__))
    if file.endswith(".py") and file not in key_files
]
