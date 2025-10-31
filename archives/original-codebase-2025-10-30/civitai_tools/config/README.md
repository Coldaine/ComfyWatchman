# Configuration Files for Civitai Tools

This directory contains configuration files and data mappings for Civitai tooling.

## Available Files

- `known_models.json` - Model ID mappings for problematic searches

## Managing Known Models

Use the helper script `scripts/add_known_model.py` to validate and store new entries:

```bash
./scripts/add_known_model.py "Better detailed pussy and anus v3.0" 1091495 --notes "Added manually"
```

The script checks the Civitai API to verify the model and version IDs before writing to `known_models.json`. Existing entries are updated in place. Pass `--known-models-path` to operate on an alternate JSON file.
