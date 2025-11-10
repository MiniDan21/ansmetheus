# ansmetheus
## Installation UV

### for Windows
```PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### for Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | less
```

## Start project

### Clone repository
```bash
git clone https://github.com/MiniDan21/ansmetheus.git
```

### Change directory
```bash
cd ansmetheus
```

### Install packages
```bash
uv sync
```

### Run project
```bash
uv run -m main
```
