CRITICAL REQUIREMENTS. When I RUN ONE SCRIPT, QUWEN will do the following. The scripts and qwen will log all their actions with timestamps.



1. **"look through all the workflows"** - Scan workflow directory for .json files
2. **"see what nodes/models are expected"** - Parse each workflow to extract model filenames and custom node types
3. **"generate a missing list"** - Compare extracted models against local inventory
4. **"generate a download script"** - Create bash script with wget/curl commands for Civitai downloads
5. **"using civitai API search"** - Search Civitai for each missing model by name
6. **"downloads the missing ones"** - Execute downloads (automated or manual)
7. **"puts them in the right folder"** - Place models in correct ComfyUI directories (checkpoints/, loras/, etc.)

---
