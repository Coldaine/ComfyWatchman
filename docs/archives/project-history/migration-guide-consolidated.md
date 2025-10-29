# Consolidated Migration Guide (v1 to v2)

This guide provides comprehensive instructions, checklists, and reference materials for migrating from ComfyFixerSmart v1.x to the refactored v2.0 system.

---

## 1. Overview of Changes (v1 vs. v2)

Version 2.0 introduces significant architectural improvements, enhanced features, and a more robust configuration system.

| Feature | v1.x (Legacy) | v2.0 (Current) |
| :--- | :--- | :--- |
| **Processing Model** | Batch (Search all -> Download all) | Incremental (Search one -> Download immediately) |
| **Configuration** | Environment variables only | TOML file with environment variable overrides |
| **State Management** | Simple JSON file | Versioned JSON with enhanced tracking |
| **CLI** | Basic script (`comfy_fixer.py`) | Modular CLI (`comfyfixersmart.cli`) with more options |
| **Output** | Single download script, flat logs | Individual scripts, organized reports, structured logs |
| **Reliability** | No resume, manual execution | Automatic resume, better error handling |

---

## 2. Quick Reference Cheat Sheet

### One-Command Migration
*For a standard setup, this command sequence performs a complete migration with backups and validation.*
```bash
python scripts/migrate_config.py && python scripts/migrate_state.py --backup && python scripts/validate_migration.py
```

### Emergency Rollback
*If the migration fails, use this to revert to your previous state.*
```bash
python scripts/rollback.py --force
```

### Command Translation
| Old Command (v1) | New Command (v2) |
| :--- | :--- |
| `python comfy_fixer.py` | `python -m comfyfixersmart.cli` |
| `python comfy_fixer.py workflow.json` | `python -m comfyfixersmart.cli workflow.json` |

---

## 3. Pre-Migration Checklist

Before starting the migration, complete these preparation steps to ensure a smooth process.

-   **[ ] System Backup:**
    *   Create a full, timestamped backup of the project directory.
        ```bash
        cp -r . migration_backup_$(date +%Y%m%d_%H%M%S)
        ```
    *   Separately back up the `state/` directory.

-   **[ ] Environment Assessment:**
    *   Document your current ComfyUI installation path.
    *   Record any custom environment variables (`env | grep "COMFYUI"`).

-   **[ ] Dependency Check:**
    *   Ensure Python 3.8+ is available.
    *   Install new required packages for the TOML configuration system.
        ```bash
        pip install tomli tomli-w
        ```

---

## 4. Step-by-Step Migration Process

Follow these phases to execute the migration.

### Phase 1: Configuration Migration
The new system uses a `config/default.toml` file. The migration script will automatically create this from your existing environment variables.

1.  **Run the migration script:**
    ```bash
    # Perform a dry run first to see what will be created
    python scripts/migrate_config.py --dry-run

    # Run the actual migration
    python scripts/migrate_config.py
    ```
2.  **Verify the new config file:**
    *   Check that `config/default.toml` has been created.
    *   Review the file to ensure your paths and settings were migrated correctly.

### Phase 2: State Migration
Your download history will be migrated to a new, more robust format.

1.  **Run the state migration script with backup:**
    ```bash
    # Perform a dry run to see the changes
    python scripts/migrate_state.py --backup --dry-run

    # Run the migration, which creates a backup automatically
    python scripts/migrate_state.py --backup
    ```
2.  **Verify the migration:**
    *   Confirm that a backup directory (`state_backup_*`) has been created.
    *   Check for the new state file: `state/download_state_v2.json`.

### Phase 3: System Validation
After migrating, run the validation script to ensure everything is working correctly.

1.  **Run the validation script:**
    ```bash
    # Run with verbose output for detailed checks
    python scripts/validate_migration.py --verbose
    ```
2.  **Perform a functional test:**
    *   Test the new CLI to ensure it responds.
        ```bash
        python -m comfyfixersmart.cli --help
        ```
    *   Run a dry run on a sample workflow to test the full pipeline.
        ```bash
        python -m comfyfixersmart.cli path/to/workflow.json --dry-run
        ```

### Phase 4: Post-Migration Cleanup
Once you have confirmed the new system is stable and working as expected:

1.  **Update Scripts and Aliases:**
    *   Change any custom scripts or shell aliases from `python comfy_fixer.py` to `python -m comfyfixersmart.cli`.
2.  **Archive Old State:**
    *   Move the old `state/download_state.json` to an archive location.
3.  **Remove Backups:**
    *   After a few days of successful operation, you can remove the `migration_backup_*` and `state_backup_*` directories.

---

## 5. Release Plan & Testing Strategy

This migration is part of the v2.0 release, which has undergone a rigorous testing process.

*   **Migration Testing:** Scenarios including fresh installs, legacy systems with data, and complex configurations have been tested.
*   **Functional Testing:** The new CLI, workflow processing, and compatibility layers have been validated.
*   **Performance Testing:** Benchmarks confirm that v2.0 is significantly faster and uses less memory than v1.x.
*   **Rollback Testing:** The emergency rollback procedures have been tested to ensure data integrity.

---

## 6. Troubleshooting

### Common Migration Issues

*   **"Import Errors"**: Your Python path may be incorrect. Set it or reinstall in editable mode.
    ```bash
    export PYTHONPATH="$PWD/src:$PYTHONPATH"
    pip install -e .
    ```
*   **"Config Not Found"**: The migration script failed or was skipped. Run it manually.
    ```bash
    python scripts/migrate_config.py --force
    ```
*   **"State Migration Fails"**: The old state file may be corrupted. Verify its JSON format.
    ```bash
    python -c "import json; json.load(open('state/download_state.json'))"
    ```

### Emergency Rollback
If the new system is not working correctly, you can revert to the previous version.

1.  **Run the rollback script:**
    ```bash
    python scripts/rollback.py --force
    ```
2.  **Reinstall the old version:**
    ```bash
    pip install comfyfixersmart==1.9.0 # Or your previous version
    ```
