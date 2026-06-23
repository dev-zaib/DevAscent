# P1-02: Rename `hermes` → `devascent` Across Codebase

**Status:** ⬜ todo
**Phase:** 1 — Foundation
**Depends on:** P1-01 (strip first so fewer files to rename)
**Blocks:** P1-03, P1-04

## Goal
Rebrand the fork from Hermes Agent to DevAscent. Rename all user-facing and internal references. This must be surgical — broken imports cascade across 5000+ files.

## AC
- [ ] Python package renamed: `import hermes_xxx` → `import devascent_xxx`
- [ ] CLI command: `hermes` → `devascent` (for remaining CLI subcommands we keep)
- [ ] Config directory: `~/.devascent` → `~/.devascent`
- [ ] Env vars: `DEVASCENT_*` → `DEVASCENT_*`
- [ ] Python module names: `devascent_state.py` → `devascent_state.py`, etc.
- [ ] `pyproject.toml`: name, version, description, scripts updated
- [ ] `package.json`: name, description, repo URLs updated
- [ ] `docker-compose.yml`: service names, image names updated
- [ ] Dockerfile: labels, paths updated
- [ ] Website references updated (or stripped)
- [ ] All imports pass after rename
- [ ] `scripts/run_tests.sh` passes

## Rename Map

### Core files (top-level)
```
hermes → devascent
devascent_bootstrap.py → devascent_bootstrap.py
devascent_constants.py → devascent_constants.py
devascent_state.py → devascent_state.py
devascent_logging.py → devascent_logging.py
devascent_time.py → devascent_time.py
devascent_cli/ → devascent_cli/
setup-devascent.sh → setup-devascent.sh
```

### Python imports (find & replace)
```
from devascent_constants import → from devascent_constants import
from devascent_state import → from devascent_state import
import devascent_constants → import devascent_constants
```

### Env vars
```
DEVASCENT_HOME → DEVASCENT_HOME
DEVASCENT_* → DEVASCENT_* (all platform/feature env vars)
```

### Config
```
~/.devascent/config.yaml → ~/.devascent/config.yaml
~/.devascent/.env → ~/.devascent/.env
~/.devascent/logs/ → ~/.devascent/logs/
```

### pyproject.toml
```toml
name = "devascent"
version = "0.1.0"
description = "The elite engineering assessment platform"
scripts:
  devascent = "devascent_cli.main:main"  # keep if we keep any CLI
```

### package.json
```json
"name": "devascent",
"repository": "git+https://github.com/dev-zaib/DevAscent.git"
```

### Docker
```
hermes-agent → devascent
~/.devascent:/opt/data → ~/.devascent:/opt/data
```

## Approach
1. Run `rg -l 'hermes' --type py` to find all Python files with references
2. Run `rg -l 'HERMES'` for env var references
3. Run `rg -l 'hermes-agent'` for package/docs references
4. Create rename script that handles:
   - Case-sensitive replacement (`hermes` → `devascent`)
   - Env var case (`HERMES` → `DEVASCENT`)
   - Package name case (`hermes-agent` → `devascent`)
   - File renaming (top-level modules)
5. Run rename, then fix any broken imports manually
6. Verify: `python -c "import devascent_state; import devascent_constants"`