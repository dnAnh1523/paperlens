# Troubleshooting

## Docker filled the C drive

PaperLens no longer requires Docker for local development.

Useful inspection command:

```powershell
docker system df
```

Destructive cleanup command, only if you no longer need existing Docker containers, images, build cache, or volumes:

```powershell
docker system prune -a --volumes
```

Docker Desktop stores WSL2 engine data under the Windows user profile by default. If Docker is used again later, move Docker Desktop disk data to a non-C drive through Docker Desktop settings.

## Backend install is slow

Use `--no-cache-dir` to reduce pip cache usage.

```powershell
python -m pip install --no-cache-dir -e .[dev]
```

## Frontend install consumes C drive cache

Set npm cache to a non-C drive before installing.

```powershell
$env:NPM_CONFIG_CACHE="F:\paperlens-npm-cache"; npm install
```
