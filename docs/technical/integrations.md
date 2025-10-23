# Integrations Guide

This guide covers integrating ComfyFixerSmart with other tools, systems, and workflows.

## ComfyUI Integration

### Standard ComfyUI Setup

ComfyFixerSmart works with standard ComfyUI installations:

```
ComfyUI/
├── models/
│   ├── checkpoints/
│   ├── loras/
│   ├── vae/
│   └── controlnet/
├── custom_nodes/
├── user/
│   └── default/
│       └── workflows/
└── output/
```

**Configuration:**
```toml
comfyui_root = "/path/to/ComfyUI"
workflow_dirs = ["user/default/workflows"]
```

### Custom ComfyUI Layouts

For non-standard layouts:

```toml
# Custom model directories
model_directories = [
    { type = "checkpoint", path = "models/stable-diffusion" },
    { type = "lora", path = "models/adapters" },
]

# Multiple workflow locations
workflow_dirs = [
    "workflows/personal",
    "workflows/shared",
    "/external/workflow/library"
]
```

### ComfyUI Manager Integration

ComfyFixerSmart complements ComfyUI Manager:

- **ComfyUI Manager**: Installs and manages custom nodes
- **ComfyFixerSmart**: Downloads missing models referenced by workflows

**Workflow:**
1. Use ComfyUI Manager to install custom nodes
2. Use ComfyFixerSmart to download required models
3. Run workflows with all dependencies satisfied

## CI/CD Integration

### GitHub Actions

**Basic Workflow Analysis:**
```yaml
name: Check Workflows
on: [push, pull_request]

jobs:
  check-workflows:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install ComfyFixerSmart
      run: pip install comfyfixersmart
    - name: Check workflows
      env:
        CIVITAI_API_KEY: ${{ secrets.CIVITAI_API_KEY }}
      run: |
        mkdir -p test-comfyui/user/default/workflows
        cp workflows/*.json test-comfyui/user/default/workflows/
        comfyfixer --comfyui-root test-comfyui --dry-run
```

**Automated Model Updates:**
```yaml
name: Update Models
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  update-models:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Update models
      env:
        CIVITAI_API_KEY: ${{ secrets.CIVITAI_API_KEY }}
      run: |
        comfyfixer --output-dir models/
        if [ -f "models/download_missing.sh" ]; then
          bash models/download_missing.sh
          git add models/
          git commit -m "Update models [automated]"
          git push
        fi
```

### GitLab CI

```yaml
stages:
  - test
  - deploy

workflow_check:
  stage: test
  script:
    - pip install comfyfixersmart
    - mkdir -p test-comfyui/user/default/workflows
    - cp workflows/*.json test-comfyui/user/default/workflows/
    - CIVITAI_API_KEY=$CIVITAI_API_KEY comfyfixer --comfyui-root test-comfyui --validate-config

model_update:
  stage: deploy
  script:
    - pip install comfyfixersmart
    - CIVITAI_API_KEY=$CIVITAI_API_KEY comfyfixer
    - bash output/download_missing.sh || true
  only:
    - schedules
```

### Docker Integration

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

# Install ComfyFixerSmart
RUN pip install comfyfixersmart

# Set up directories
RUN mkdir -p /comfyui /workflows /output

# Copy configuration
COPY config/default.toml /config/default.toml

# Set environment
ENV COMFYUI_ROOT=/comfyui
ENV CONFIG_FILE=/config/default.toml

# Run ComfyFixerSmart
CMD ["comfyfixer", "--output-dir", "/output"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  comfyfixer:
    build: .
    volumes:
      - ./comfyui:/comfyui
      - ./workflows:/workflows
      - ./output:/output
    environment:
      - CIVITAI_API_KEY=${CIVITAI_API_KEY}
    command: ["comfyfixer", "--dir", "/workflows"]
```

## API Integration

### REST API Usage

ComfyFixerSmart can be integrated into REST APIs:

```python
from flask import Flask, request, jsonify
from comfyfixersmart import ComfyFixerCore
import asyncio

app = Flask(__name__)
fixer = ComfyFixerCore()

@app.route('/analyze', methods=['POST'])
def analyze_workflows():
    data = request.json
    workflow_paths = data.get('workflows', [])

    # Run analysis asynchronously
    result = asyncio.run(run_analysis_async(workflow_paths))

    return jsonify({
        'status': 'success',
        'missing_models': result.models_missing,
        'available_models': result.models_found
    })

async def run_analysis_async(workflow_paths):
    # Run in thread pool to avoid blocking
    return await asyncio.get_event_loop().run_in_executor(
        None, fixer.run, workflow_paths
    )

if __name__ == '__main__':
    app.run()
```

### Webhook Integration

Receive notifications when models are missing:

```python
import requests
from comfyfixersmart import ComfyFixerCore

class WebhookNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.fixer = ComfyFixerCore()

    def check_and_notify(self, workflow_path):
        result = self.fixer.run(workflow_paths=[workflow_path])

        if result.models_missing > 0:
            payload = {
                'event': 'missing_models',
                'workflow': workflow_path,
                'missing_count': result.models_missing,
                'timestamp': datetime.now().isoformat()
            }
            requests.post(self.webhook_url, json=payload)

# Usage
notifier = WebhookNotifier("https://api.example.com/webhooks/models")
notifier.check_and_notify("new_workflow.json")
```

## Model Management Systems

### Integration with Civitai Toolkit

ComfyFixerSmart works alongside Civitai Toolkit:

```python
# Use Civitai Toolkit for metadata
from civitai_toolkit import CivitaiAPI
from comfyfixersmart import ModelSearch

civitai_api = CivitaiAPI()
search = ModelSearch()

# Cross-reference models
def get_model_info_with_metadata(model_name):
    # Search with ComfyFixerSmart
    results = search.search(model_name)

    # Get additional metadata from Civitai Toolkit
    if results:
        model_id = results[0].model_id
        metadata = civitai_api.get_model_metadata(model_id)
        return {**results[0], **metadata}

    return None
```

### Integration with LoRA Manager

Complements existing LoRA management tools:

```python
# Coordinate with lora-manager
from comfyfixersmart import DownloadManager
from lora_manager import LoRAManager

download_manager = DownloadManager()
lora_manager = LoRAManager()

def download_and_register_loras(missing_loras):
    for lora in missing_loras:
        # Download with ComfyFixerSmart
        result = download_manager.download_model(lora.download_url, lora.save_path)

        if result.success:
            # Register with LoRA Manager
            lora_manager.register_lora(lora.save_path, lora.metadata)
```

## Civitai API Integration

### API Quirks and Validation

ComfyFixerSmart integrates with the Civitai API for model discovery and metadata. However, the Civitai API has some undocumented behaviors that require defensive programming.

#### Known API Quirks

**1. Image Endpoint ID Mismatch**

The `/api/v1/images?ids={id}` endpoint may return a different image instead of returning a 404 when the requested image ID doesn't exist.

```python
# WRONG - May return wrong image
response = requests.get(f"https://civitai.com/api/v1/images?ids={image_id}")
data = response.json()
result = data['items'][0]  # Could be wrong image!

# CORRECT - Validate returned ID
from comfyfixersmart.utils import validate_civitai_response

response = requests.get(f"https://civitai.com/api/v1/images?ids={image_id}")
data = response.json()

validation = validate_civitai_response(data, requested_id=image_id, endpoint_type='images')
if not validation['valid']:
    raise ValueError(validation['error_message'])

result = data['items'][0]  # Now guaranteed to be correct
```

**Real Incident:**
- Requested image ID: `96712457`
- API returned image ID: `9173928` (different image!)
- Result: Downloaded wrong models, created wrong workflow
- See: `docs/reports/civitai-api-wrong-metadata-incident.md`

**2. Endpoint Comparison**

| Endpoint | Missing ID Behavior | Recommended |
|----------|---------------------|-------------|
| `/api/v1/images/{id}` | Returns 404 | ✅ Use for single image |
| `/api/v1/images?ids={id}` | Returns different image | ⚠️ Requires validation |
| `/api/v1/models/{id}` | Returns 404 | ✅ Safe to use |

#### Validation Utilities

**validate_civitai_response()**

Validates that API responses match requested IDs:

```python
from comfyfixersmart.utils import validate_civitai_response

# Validate model endpoint response
response_data = api.get(f"/models/{model_id}").json()
validation = validate_civitai_response(
    response_data,
    requested_id=model_id,
    endpoint_type='model'
)

if not validation['valid']:
    print(f"Error: {validation['error_message']}")
    # Handle mismatch

# Validate images endpoint response
response_data = api.get(f"/images?ids={image_id}").json()
validation = validate_civitai_response(
    response_data,
    requested_id=image_id,
    endpoint_type='images'
)

if not validation['valid']:
    print(f"Error: {validation['error_message']}")
    # Handle mismatch (deleted/restricted image)
```

**fetch_civitai_image()**

Safe image fetching with built-in validation:

```python
from comfyfixersmart.utils import fetch_civitai_image

try:
    image_data = fetch_civitai_image(96712457)
    print(f"Prompt: {image_data['meta']['prompt']}")
    print(f"URL: {image_data['url']}")
except ValueError as e:
    print(f"Image fetch failed: {e}")
    # Image may be deleted or restricted
```

#### Error Messages

The validation utilities provide detailed error messages:

```
API returned wrong image. Requested: 96712457, Got: 9173928.
This image may have been deleted or is restricted.
```

```
API returned wrong model. Requested: 12345, Got: 67890
```

```
Image 96712457 not found (empty items array)
```

#### Best Practices for Civitai API

1. **Always Validate IDs:**
   - Never trust that returned ID matches requested ID
   - Use `validate_civitai_response()` for all API calls

2. **Handle Missing Resources:**
   ```python
   try:
       image = fetch_civitai_image(image_id)
   except ValueError as e:
       if "not found" in str(e).lower():
           # Resource deleted or restricted
           log_warning(f"Image {image_id} unavailable: {e}")
       else:
           # ID mismatch or other error
           log_error(f"Unexpected error: {e}")
           raise
   ```

3. **Log API Interactions:**
   ```python
   logger.debug(f"Requested image ID: {image_id}")
   logger.debug(f"Received image ID: {result['id']}")
   logger.debug(f"Image URL: {result.get('url')}")
   ```

4. **Implement Retry Logic:**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def safe_fetch_model(model_id):
       response = requests.get(f"https://civitai.com/api/v1/models/{model_id}")
       data = response.json()

       validation = validate_civitai_response(data, requested_id=model_id, endpoint_type='model')
       if not validation['valid']:
           raise ValueError(validation['error_message'])

       return data
   ```

5. **Cache Validated Responses:**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def cached_fetch_image(image_id):
       return fetch_civitai_image(image_id)
   ```

#### Testing Validation

The test suite includes comprehensive validation tests:

```bash
# Run Civitai API validation tests
pytest tests/unit/test_utils.py::TestCivitaiAPIValidation -v
```

Tests cover:
- Valid responses (IDs match)
- ID mismatches (the incident scenario)
- Empty responses (deleted resources)
- HTTP errors (404, 500, etc.)

See `tests/unit/test_utils.py` for complete test cases.

#### Related Documentation

- **Incident Report:** `docs/reports/civitai-api-wrong-metadata-incident.md`
- **Utility Functions:** `src/comfyfixersmart/utils.py`
- **Test Cases:** `tests/unit/test_utils.py::TestCivitaiAPIValidation`
- **Search Implementation:** `src/comfyfixersmart/search.py`

## Workflow Management

### Integration with Git

**Version Control for Workflows:**
```bash
# Track workflow changes
git add workflows/
git commit -m "Add new SDXL workflow"

# Check for missing models before commit
comfyfixer --dry-run
if [ $? -eq 0 ]; then
    git commit -m "Add workflow with all models available"
else
    echo "Missing models - run comfyfixer first"
    exit 1
fi
```

**GitHub Integration:**
```yaml
name: Validate Workflows
on:
  pull_request:
    paths:
      - 'workflows/*.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Validate workflows
      run: |
        pip install comfyfixersmart
        comfyfixer --validate-config
        comfyfixer --dry-run --dir workflows/
```

### Integration with Workflow Repositories

**Automatic Sync:**
```bash
#!/bin/bash
# sync_workflows.sh

# Pull latest workflows
git pull origin main

# Check for missing models
comfyfixer --output-dir sync/

if [ -f "sync/download_missing.sh" ]; then
    echo "New missing models found"
    bash sync/download_missing.sh

    # Update model registry
    ./update_model_registry.py
fi
```

## Monitoring and Alerting

### Prometheus Integration

```python
from prometheus_client import Counter, Histogram, start_http_server
from comfyfixersmart import ComfyFixerCore

# Metrics
MODELS_DOWNLOADED = Counter('comfyfixer_models_downloaded_total', 'Total models downloaded')
ANALYSIS_DURATION = Histogram('comfyfixer_analysis_duration_seconds', 'Analysis duration')

class MonitoredComfyFixer:
    def __init__(self):
        self.fixer = ComfyFixerCore()

    def run_with_metrics(self, *args, **kwargs):
        with ANALYSIS_DURATION.time():
            result = self.fixer.run(*args, **kwargs)

        MODELS_DOWNLOADED.inc(result.models_resolved)
        return result

# Start metrics server
start_http_server(8000)

# Use monitored fixer
fixer = MonitoredComfyFixer()
result = fixer.run_with_metrics(workflow_paths=["workflow.json"])
```

### Log Aggregation

**ELK Stack Integration:**
```python
import logging
from elasticsearch import Elasticsearch

class ElasticsearchHandler(logging.Handler):
    def __init__(self, es_host):
        super().__init__()
        self.es = Elasticsearch([es_host])

    def emit(self, record):
        log_entry = {
            'timestamp': record.created,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        self.es.index(index='comfyfixer-logs', body=log_entry)

# Configure logging
logger = logging.getLogger()
handler = ElasticsearchHandler('localhost:9200')
logger.addHandler(handler)
```

### Alert Manager Integration

```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'comfyfixer-alerts'

receivers:
- name: 'comfyfixer-alerts'
  webhook_configs:
  - url: 'http://alerts.example.com/webhook'
    send_resolved: true
```

## Custom Backend Integration

### Adding Custom Search Backends

```python
from comfyfixersmart.search import SearchBackend, SearchResult

class CustomBackend(SearchBackend):
    name = "custom"

    def search(self, query, model_type=None):
        # Implement custom search logic
        # Return list of SearchResult objects
        pass

    def get_model_details(self, model_id):
        # Get detailed model information
        pass

# Register backend
from comfyfixersmart import ModelSearch
search = ModelSearch()
search.add_backend(CustomBackend())

# Use in configuration
# search_backends = ["civitai", "custom"]
```

### Custom Download Handlers

```python
from comfyfixersmart.download import DownloadHandler

class CustomDownloader(DownloadHandler):
    def download(self, url, save_path, progress_callback=None):
        # Implement custom download logic
        pass

    def supports_url(self, url):
        # Return True if this handler can download the URL
        return url.startswith("custom://")

# Register handler
from comfyfixersmart import DownloadManager
manager = DownloadManager()
manager.add_handler(CustomDownloader())
```

## Enterprise Integration

### LDAP/Active Directory

```python
import ldap
from comfyfixersmart.config import config

class LDAPAuthenticator:
    def __init__(self, ldap_server):
        self.ldap_server = ldap_server

    def authenticate(self, username, password):
        # LDAP authentication logic
        pass

# Integration example
auth = LDAPAuthenticator("ldap://company.com")
if auth.authenticate(os.getenv('USERNAME'), os.getenv('PASSWORD')):
    # Allow ComfyFixerSmart execution
    result = fixer.run()
```

### Audit Logging

```python
import json
from datetime import datetime
from comfyfixersmart import ComfyFixerCore

class AuditLogger:
    def __init__(self, audit_file):
        self.audit_file = audit_file

    def log_operation(self, operation, user, details):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'operation': operation,
            'details': details
        }

        with open(self.audit_file, 'a') as f:
            json.dump(entry, f)
            f.write('\n')

# Usage
audit = AuditLogger('/var/log/comfyfixer_audit.log')
fixer = ComfyFixerCore()

# Before operation
audit.log_operation('start_analysis', os.getenv('USER'), {'workflow_count': 5})

result = fixer.run()

# After operation
audit.log_operation('complete_analysis', os.getenv('USER'), {
    'models_found': result.models_found,
    'models_downloaded': result.models_resolved
})
```

## Civitai API Safeguards

The incident documented in `docs/reports/civitai-api-wrong-metadata-incident.md` is now part of our baseline operating procedures. All integrations that call `https://civitai.com/api/v1/images` **must**:

1. Validate that the returned `items[0].id` exactly matches the requested image ID. If it does not, raise an explicit error instead of using the response.
2. Treat empty `items` arrays or mismatched IDs as hard failures and surface a clear `NOT_FOUND / possibly deleted` message to the caller.
3. Log the requested ID, returned ID, and any URLs at DEBUG level so future mismatches are traceable.
4. Use a shared helper (to be added under `src/comfyfixersmart/utils.py`) such as `validate_civitai_image_response(image_id, payload)` to centralise the guardrails.

Until this helper ships, do **not** build new features that rely on the Civitai Images endpoint.

## Best Practices

### Integration Patterns

1. **Loose Coupling**: Use events/webhooks rather than tight integration
2. **Error Handling**: Implement circuit breakers for external services
3. **Configuration**: Keep integration settings separate from core config
4. **Testing**: Mock external services in integration tests

### Security Considerations

1. **API Keys**: Store securely, rotate regularly
2. **Network**: Use HTTPS for all external communications
3. **Access Control**: Implement proper authentication/authorization
4. **Audit**: Log all integration activities

### Performance Optimization

1. **Caching**: Cache external API responses
2. **Async**: Use async operations for I/O bound tasks
3. **Batching**: Group operations to reduce overhead
4. **Monitoring**: Track integration performance metrics

This integrations guide provides patterns and examples for connecting ComfyFixerSmart with various systems and workflows in your environment.
