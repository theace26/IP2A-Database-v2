# Devcontainer Fix Instructions

## Files to Update

Copy these files to your project:

| Source File | Destination |
|-------------|-------------|
| `docker-compose.yml` | `~/Projects/IP2A-Database-v2/docker-compose.yml` |
| `Dockerfile` | `~/Projects/IP2A-Database-v2/Dockerfile` |
| `devcontainer.json` | `~/Projects/IP2A-Database-v2/.devcontainer/devcontainer.json` |
| `.dockerignore` | `~/Projects/IP2A-Database-v2/.dockerignore` |

## Quick Commands (Run on Mac Terminal)

```bash
# Set project path variable for this session
export IP2A=~/Projects/IP2A-Database-v2

# Stop current containers
cd $IP2A && docker-compose down

# Backup existing files (just in case)
mkdir -p $IP2A/.backup
cp $IP2A/docker-compose.yml $IP2A/.backup/
cp $IP2A/Dockerfile $IP2A/.backup/
cp $IP2A/.devcontainer/devcontainer.json $IP2A/.backup/

# After copying new files, rebuild
cd $IP2A && docker-compose build --no-cache

# Start containers
cd $IP2A && docker-compose up -d

# Verify everything is running
docker ps

# Rebuild devcontainer in VS Code
# Cmd+Shift+P → "Dev Containers: Rebuild Container"
```

## What Changed

### docker-compose.yml
- **Full project mount**: `.:/app:cached` instead of selective mounts
- **Cache exclusions**: Prevents `__pycache__`, `.pytest_cache`, `.ruff_cache` from syncing
- **Build target**: Uses `development` stage from Dockerfile

### Dockerfile
- **Multi-stage build**: Separate `development` and `production` stages
- **Dev stage**: No code copied (mounted via docker-compose)
- **Prod stage**: Code baked in, runs as non-root user

### devcontainer.json
- **More extensions**: Ruff, GitLens, SQLTools, spell checker
- **Better settings**: Format on save, Ruff integration
- **Port forwarding**: FastAPI (8000), PostgreSQL (5433), pgAdmin (5050)
- **SQLTools connection**: Pre-configured database connection

### .dockerignore
- **Faster builds**: Excludes unnecessary files from Docker context
- **Smaller images**: No `.git`, `__pycache__`, `.vscode`, etc.

## Verification

After rebuild, test that files sync properly:

```bash
# Create a test file on Mac
echo "test" > $IP2A/test-sync.txt

# In devcontainer, check it exists
cat /app/test-sync.txt  # Should show "test"

# Create a file in devcontainer
echo "from-container" > /app/test-from-container.txt

# On Mac, verify it synced
cat $IP2A/test-from-container.txt  # Should show "from-container"

# Cleanup
rm $IP2A/test-sync.txt $IP2A/test-from-container.txt
```

## Troubleshooting

**Container won't start?**
```bash
docker-compose logs api
```

**Permission issues?**
```bash
# Fix ownership on Mac
sudo chown -R $(whoami) $IP2A
```

**Need to fully reset?**
```bash
cd $IP2A
docker-compose down -v  # Warning: removes database data too!
docker system prune -f
docker-compose up -d --build
```
