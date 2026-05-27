## Summary
- add direct-id known model helper, CLI tool, and docs pointers for fast seeding
- replace Qwen backend stub with real CLI integration, caching, and manual harness
- detect textual inversion embeddings end-to-end (scan → search → download) + workflow helper
- introduce optional background scheduler with VRAM guard and CLI switches

## Verification
- python -m compileall src/comfywatchman/search.py src/comfywatchman/config.py src/comfywatchman/scheduler.py scripts/add_known_model.py scripts/run_qwen_search.py scripts/find_embeddings.py
