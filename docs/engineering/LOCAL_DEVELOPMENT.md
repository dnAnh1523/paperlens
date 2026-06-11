# Local Development Without Docker

PaperLens uses local-native development on Windows 11.

## Backend

```powershell
cd apps/api
```

```powershell
py -3.12 -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install --no-cache-dir -e .[dev]
```

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```powershell
cd apps/web
```

```powershell
npm install
```

```powershell
npm run dev
```

## Disk-space notes

Keep the repository, Python virtual environment, Node modules, and generated data on a non-C drive.
