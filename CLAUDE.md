
---

## Cross-Platform Setup

### Required on Each New Machine

**.env.compose** - Not in git (contains credentials). Create from template:
```bash
# Mac/Linux
cp .env.compose.example .env.compose

# Windows PowerShell
Copy-Item .env.compose.example .env.compose
```

### Path Shortcuts

| OS | Command | Path |
|----|---------|------|
| Mac | `` | `~/Projects/IP2A-Database-v2` |
| Windows | `C:\Users\Xerxes\Projects\IP2A-Database-v2` | `~\Projects\IP2A-Database-v2` |

Add to shell profile:
- **Mac** (~/.zshrc): `export IP2A=~/Projects/IP2A-Database-v2`
- **Windows** (D:\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1): `C:\Users\Xerxes\Projects\IP2A-Database-v2 = "C:\Users\Xerxes\Projects\IP2A-Database-v2"`

### Switching Machines Workflow
```bash
# Before leaving current machine
git add -A && git commit -m "WIP: current state" && git push

# On new machine
git pull
# Ensure .env.compose exists (copy from .env.compose.example if needed)
docker-compose up -d
# VS Code: Ctrl/Cmd+Shift+P → "Dev Containers: Reopen in Container"
```
