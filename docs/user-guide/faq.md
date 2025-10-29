# Frequently Asked Questions

This FAQ covers common questions about ComfyFixerSmart usage, troubleshooting, and development.

## General Questions

### What is ComfyFixerSmart?

ComfyFixerSmart is an intelligent tool that analyzes ComfyUI workflow files, identifies missing models and custom nodes, searches for replacements on Civitai and HuggingFace, and automatically downloads them to the correct directories.

**Key Features:**
- Automatic workflow analysis
- Intelligent model search and matching
- Incremental download system (v2.0)
- Comprehensive error handling and reporting

### How does it differ from ComfyUI Manager?

| Feature | ComfyUI Manager | ComfyFixerSmart |
|---------|----------------|------------------|
| **Purpose** | Custom node management | Model dependency resolution |
| **Scope** | Nodes, extensions | Models, checkpoints, LoRAs |
| **Operation** | Interactive installation | Automated batch processing |
| **Integration** | ComfyUI built-in | Standalone tool |

**Use them together:** ComfyUI Manager for nodes, ComfyFixerSmart for models.

### What versions of ComfyUI are supported?

- **ComfyUI 1.0+**: Fully supported
- **Custom nodes**: Automatic detection
- **Workflow formats**: JSON workflows
- **Model types**: All standard ComfyUI model types

### Is it free to use?

Yes, ComfyFixerSmart is open-source software released under the MIT License. However, you need:

- **Civitai API Key**: Free account required
- **HuggingFace Token**: Optional, for private models
- **ComfyUI Installation**: The tool analyzes and enhances existing setups

## Installation & Setup

### Do I need to install ComfyUI first?

Yes, ComfyFixerSmart requires an existing ComfyUI installation to analyze. It doesn't install ComfyUI itself.

**Minimum ComfyUI Setup:**
```bash
# Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
```

### Can I use it without Civitai API key?

No, a Civitai API key is required for model downloads. The API key is free but requires a Civitai account.

**Get API Key:**
1. Visit https://civitai.com/user/account
2. Generate a new API key
3. Set environment variable: `export CIVITAI_API_KEY="your-key"`

### What are the system requirements?

**Minimum:**
- Python 3.7+
- 4GB RAM
- 10 Mbps internet
- 100MB disk space

**Recommended:**
- Python 3.9+
- 8GB RAM
- 50 Mbps internet
- 500MB SSD storage

### Can it run on Windows/macOS?

Yes, ComfyFixerSmart is cross-platform:

- **Windows**: Native support via Python
- **macOS**: Native support
- **Linux**: Fully supported

**Windows Installation:**
```bash
# Use PowerShell or cmd
pip install comfyfixersmart

# Set environment variables
set CIVITAI_API_KEY=your-key
set COMFYUI_ROOT=C:\path\to\ComfyUI
```

## Usage Questions

### How do I analyze a single workflow?

```bash
comfyfixer path/to/workflow.json
```

This will:
1. Parse the workflow
2. Check for missing models
3. Search Civitai for replacements
4. Generate download script

### How do I analyze all workflows in a directory?

```bash
comfyfixer --dir /path/to/workflows/
```

Or configure default directories:
```toml
# config/default.toml
workflow_dirs = [
    "user/default/workflows",
    "custom/workflows"
]
```

### What if models are already downloaded?

ComfyFixerSmart checks your existing model inventory and only downloads missing models. It won't re-download existing files.

### Can it handle custom model directories?

Yes, configure custom model paths:
```toml
model_directories = [
    { type = "checkpoint", path = "models/stable-diffusion" },
    { type = "lora", path = "models/adapters" },
]
```

### What model types are supported?

**Supported Model Types:**
- Checkpoints (`.safetensors`, `.ckpt`)
- LoRAs (`.safetensors`)
- VAEs (`.safetensors`, `.pt`)
- ControlNets (`.safetensors`, `.pth`)
- Upscale models (`.pth`)
- CLIP models (`.safetensors`)
- Embeddings (`.pt`, `.bin`)

### Does it support HuggingFace models?

Yes, as a secondary search backend:
```bash
comfyfixer --search civitai,huggingface
```

**Requirements:**
- Optional HuggingFace token for private models
- Automatic fallback if Civitai search fails

## Performance & Reliability

### Why is it slow for many models?

**Performance Factors:**
- **API Rate Limits**: Civitai limits requests
- **Network Speed**: Large model downloads
- **Concurrent Downloads**: Limited by configuration

**Optimizations:**
```toml
# Increase concurrency for fast networks
download_concurrency = 5

# Enable caching
cache_enabled = true
```

### What if downloads fail?

ComfyFixerSmart includes robust error handling:

- **Automatic Retries**: Failed downloads retry automatically
- **Resume Support**: Interrupted downloads can resume
- **Verification**: Downloaded files are verified
- **Fallback Options**: Alternative download methods

### Can I resume interrupted operations?

Yes, v2.0 includes resume support:
```bash
comfyfixer --resume
```

This will:
- Skip already downloaded models
- Resume partial downloads
- Continue from last successful point

### How much disk space do I need?

**Base Installation:** 100MB
**Model Downloads:** Varies greatly

**Typical Usage:**
- SDXL Checkpoint: 6-7GB
- Large LoRA Collection: 10-50GB
- Full Model Library: 100GB+

**Plan for:** 2-3x your current model collection size.

## Configuration Questions

### Where should I put the config file?

**Recommended Locations:**
- `config/default.toml` (project-specific)
- `~/.config/comfyfixersmart/config.toml` (user-specific)

**Priority Order:**
1. `--config` command-line option
2. Environment variables
3. `config/default.toml`
4. Default values

### Can I use environment variables instead of config files?

Yes, all configuration can be done via environment variables:

```bash
export COMFYUI_ROOT="/path/to/comfyui"
export CIVITAI_API_KEY="your-key"
export DOWNLOAD_CONCURRENCY="3"
export LOG_LEVEL="INFO"
```

### How do I configure multiple ComfyUI instances?

Use different configuration files:
```bash
# Instance 1
comfyfixer --config config/instance1.toml

# Instance 2
comfyfixer --config config/instance2.toml
```

Each config can point to different ComfyUI installations.

## Troubleshooting

### "No workflows found"

**Check:**
- Workflow files end with `.json`
- Files contain valid ComfyUI workflow JSON
- Directory permissions allow reading
- Path is correct (use absolute paths if needed)

**Debug:**
```bash
find /path/to/workflows -name "*.json"
comfyfixer --log-level DEBUG --dir /path/to/workflows
```

### "Civitai API key not found"

**Check:**
- Environment variable is set: `echo $CIVITAI_API_KEY`
- Variable is exported: `export CIVITAI_API_KEY=your-key`
- No extra spaces or characters
- Key is valid (test with curl)

**Test Key:**
```bash
curl -H "Authorization: Bearer $CIVITAI_API_KEY" \
     https://civitai.com/api/v1/models?limit=1
```

### "Permission denied"

**Check:**
- Write permissions on model directories
- ComfyUI model folder ownership
- Run as appropriate user or use sudo

**Fix:**
```bash
# Fix permissions
chmod -R u+w /path/to/comfyui/models/
# Or change ownership
sudo chown -R $USER:$USER /path/to/comfyui/
```

### "Out of memory"

**Solutions:**
- Reduce download concurrency: `--concurrency 1`
- Process fewer workflows at once
- Increase system RAM
- Use `--cache-enabled false` to reduce memory usage

### "Model not found on Civitai"

**Possible Reasons:**
- Model was removed or renamed
- Typo in workflow filename
- Model is from a different source
- API search limitations

**Solutions:**
- Check Civitai website manually
- Use HuggingFace backend as fallback
- Update workflow with correct filename
- Report missing models to maintainers

## Development Questions

### How do I contribute?

**Contribution Process:**
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request
5. Code review and merge

**Requirements:**
- Tests pass (`pytest`)
- Code formatted (`black`)
- Type hints added
- Documentation updated

### Can I add custom search backends?

Yes, implement the `SearchBackend` interface:

```python
from comfyfixersmart.search import SearchBackend

class MyBackend(SearchBackend):
    name = "mybackend"

    def search(self, query, model_type=None):
        # Implement search logic
        return [SearchResult(...)]

# Register backend
search.add_backend(MyBackend())
```

### How do I run tests?

```bash
# Install development dependencies
pip install -e .[dev]

# Run all tests
pytest

# Run with coverage
pytest --cov=comfyfixersmart

# Run specific tests
pytest tests/unit/test_config.py
```

### What's the difference between v1 and v2?

**v1.x (Legacy):**
- Batch processing (search all → download all)
- No caching
- Manual script execution
- Higher memory usage

**v2.0 (Current):**
- Incremental processing (search one → download immediately)
- Intelligent caching
- Automatic execution
- Better performance and reliability

**Migration:** Automatic, but see migration guide for details.

## Advanced Usage

### Can I use it programmatically?

Yes, full Python API available:

```python
from comfyfixersmart import ComfyFixerCore

fixer = ComfyFixerCore()
result = fixer.run(
    workflow_paths=["workflow.json"],
    output_dir="output/"
)
```

### How do I integrate with CI/CD?

**GitHub Actions Example:**
```yaml
- name: Check workflows
  run: |
    pip install comfyfixersmart
    comfyfixer --validate-config
    comfyfixer --dry-run
  env:
    CIVITAI_API_KEY: ${{ secrets.CIVITAI_API_KEY }}
```

### Can it handle very large model collections?

Yes, with optimizations:

```toml
# Large collection optimizations
cache_enabled = true
download_concurrency = 2
max_workers = 4

# Process in batches
comfyfixer --dir large_collection_batch_1/
comfyfixer --dir large_collection_batch_2/
```

### What about custom node dependencies?

ComfyFixerSmart focuses on models. For custom nodes, use:

- **ComfyUI Manager**: Official node manager
- **ComfyUI-Manager**: Community tool
- Manual installation for unsupported nodes

## Security & Privacy

### Is my API key secure?

**Security Measures:**
- Keys stored locally (not transmitted to maintainers)
- HTTPS-only API communication
- No key logging in output files
- Environment variable isolation

**Best Practices:**
- Use strong, unique API keys
- Rotate keys regularly
- Don't share configuration files with keys
- Use secret management in CI/CD

### What data is sent to external services?

**API Communications:**
- Model search queries to Civitai/HuggingFace
- Download requests with authentication
- No personal workflow content transmitted
- Only model filenames and metadata

### Can I use it offline?

Limited offline support:
- Cached search results work offline
- Local model inventory checking works
- No new searches or downloads without internet

## Support & Community

### Where can I get help?

**Resources:**
- **Documentation**: This FAQ and guides
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community questions
- **Logs**: Enable debug logging for troubleshooting

### How do I report bugs?

**Bug Report Template:**
```
**Description:** Clear description of the issue
**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Expected result vs actual result

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.9.7]
- ComfyFixerSmart: [e.g., 2.0.0]

**Logs:** Attach relevant log output
```

### Are there commercial support options?

Currently community-supported. For enterprise needs:
- Open GitHub issues for feature requests
- Consider professional consulting services
- Check for commercial forks or extensions

## Future Plans

### What's coming in future versions?

**Planned Features:**
- Plugin system for custom backends
- Async/await support for better concurrency
- Enhanced model compatibility checking
- Web-based interface
- Docker container optimization

### How can I influence development?

**Community Input:**
- GitHub Issues for feature requests
- Discussions for design feedback
- Pull requests for implementations
- Bug reports with detailed information

### Will v1.x continue to be supported?

**Support Timeline:**
- v2.0+: Active development and support
- v1.x: Critical fixes until v3.0 release
- Legacy versions: Security fixes only

This FAQ covers the most common questions. For additional help, check the documentation or open a GitHub issue.