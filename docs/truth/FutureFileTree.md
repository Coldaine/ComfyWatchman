# Future File Tree Architecture

## Overview

This document explains the planned file structure after integrating ComfyUI-Copilot features with ComfyWatchman. The architecture maintains clean separation between our core functionality, the integration layer (adapters), and the forked Copilot backend.

---

## Complete File Tree

```
ComfyWatchman/
├── src/
│   ├── comfywatchman/                  # OUR CORE - Always works standalone
│   │   ├── __init__.py                 # Package initialization
│   │   ├── cli.py                      # Command-line interface entry point
│   │   ├── core.py                     # Main orchestrator (unchanged)
│   │   ├── config.py                   # Configuration management (enhanced)
│   │   ├── scanner.py                  # Workflow scanning (unchanged)
│   │   ├── inventory.py                # Local model inventory (unchanged)
│   │   ├── search.py                   # Search with backends (enhanced)
│   │   ├── download.py                 # Script generation (unchanged)
│   │   ├── state_manager.py            # JSON state management (default)
│   │   ├── logging.py                  # Logging utilities (unchanged)
│   │   └── utils.py                    # Shared utilities (unchanged)
│   │
│   ├── adapters/                        # INTEGRATION LAYER - Clean boundaries
│   │   ├── __init__.py                  # Feature detection & availability checks
│   │   ├── copilot_validator.py        # Wraps Copilot validation in our interface
│   │   ├── modelscope_search.py        # Adapts ModelScope to our search interface
│   │   ├── sql_state.py                # SQL state manager (optional alternative)
│   │   ├── repair_agent.py             # Wraps Copilot auto-repair functionality
│   │   └── base.py                     # Base adapter classes and interfaces
│   │
│   └── copilot_backend/                # FORKED COPILOT - Git submodule
│       ├── .git/                       # Submodule git tracking
│       ├── backend/                    # Core Copilot backend (pruned)
│       │   ├── service/                # Validation & repair services
│       │   │   ├── debug_agent.py      # Workflow debugging agent
│       │   │   ├── parameter_tools.py  # Parameter matching/fixing
│       │   │   ├── link_agent_tools.py # Connection repair tools
│       │   │   └── workflow_rewrite_*  # Workflow modification tools
│       │   ├── utils/                  # Utility functions
│       │   │   ├── modelscope_gateway.py # ModelScope API client
│       │   │   ├── comfy_gateway.py    # ComfyUI API interface
│       │   │   └── logger.py           # Their logging (isolated)
│       │   └── dao/                    # Data access objects
│       │       └── workflow_table.py   # SQL workflow storage
│       ├── requirements.txt            # Copilot dependencies (optional)
│       └── LICENSE                     # MIT License
│
├── config/
│   ├── default.toml                    # Default configuration
│   ├── config-example.toml             # Example with all options documented
│   └── copilot-example.toml            # Example with Copilot features enabled
│
├── tests/
│   ├── unit/
│   │   ├── test_scanner.py             # Our core tests (unchanged)
│   │   ├── test_search.py              # Enhanced with multi-backend tests
│   │   └── test_config.py              # Test feature flag system
│   ├── integration/
│   │   ├── test_adapters.py            # Test adapter integration
│   │   ├── test_validation.py          # Test Copilot validation
│   │   └── test_fallbacks.py           # Test graceful degradation
│   └── fixtures/
│       ├── workflows/                  # Test workflow files
│       └── mock_copilot/               # Mock Copilot responses
│
├── scripts/
│   ├── install_copilot.sh              # Sets up Copilot submodule
│   ├── update_copilot.sh               # Updates from upstream
│   ├── prune_copilot.sh                # Removes unnecessary files
│   └── test_integration.sh             # Runs integration test suite
│
├── docs/
│   ├── truth/                          # Strategic documents
│   │   ├── Pathforward.md              # Integration plan
│   │   └── FutureFileTree.md           # This document
│   ├── research/                       # Research & analysis
│   │   ├── copilot_analysis.md         # Copilot feature analysis
│   │   └── integration_notes.md        # Integration discoveries
│   ├── architecture.md                 # Updated architecture
│   ├── ADAPTER_GUIDE.md               # How to write adapters
│   └── COPILOT_FEATURES.md            # Guide to Copilot features
│
├── output/                              # Generated output (unchanged)
├── state/                               # State files (JSON or SQL)
├── log/                                 # Log files
├── temp/                                # Temporary files
│
├── pyproject.toml                       # Package configuration (enhanced)
├── README.md                            # Project documentation
├── CHANGELOG.md                         # Version history
├── LICENSE                              # Our license
└── .gitmodules                          # Git submodule configuration
```

---

## Directory Explanations

### `/src/comfywatchman/` - Our Core (Unchanged Philosophy)

**Purpose:** Contains all our original functionality that works completely standalone.

**Key Points:**
- **NO DEPENDENCIES** on Copilot code
- Works exactly as it does today without any Copilot features
- This is the foundation that always works offline, in batch mode
- Changes here are minimal - mainly adding hooks for adapters

**Files that change:**
- `config.py` - Adds feature flags and adapter configuration
- `search.py` - Adds ability to use additional search backends via adapters

**Files that DON'T change:**
- `cli.py` - Same CLI interface
- `scanner.py` - Same batch scanning
- `download.py` - Same script generation
- Everything else core to our functionality

---

### `/src/adapters/` - The Integration Layer (NEW)

**Purpose:** Clean boundary between our code and Copilot code. All integration happens here.

**Key Components:**

#### `__init__.py` - Feature Detection
```python
# Detects what's available at runtime
try:
    from copilot_backend import available
    COPILOT_AVAILABLE = True
except ImportError:
    COPILOT_AVAILABLE = False

try:
    import modelscope
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False
```

#### `copilot_validator.py` - Validation Adapter
```python
class CopilotValidatorAdapter:
    """Wraps Copilot's validation to work with our batch processing"""

    def validate(self, workflow_path):
        if not COPILOT_AVAILABLE:
            return None  # Graceful degradation

        try:
            # Call Copilot validation
            from copilot_backend.backend.service import debug_agent
            return debug_agent.validate(workflow_path)
        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            return None  # Don't break our tool
```

#### `modelscope_search.py` - Search Adapter
```python
class ModelScopeSearchAdapter(SearchBackend):
    """Adapts ModelScope to our SearchBackend interface"""

    def search(self, model_info):
        # Converts our model format to their format
        # Calls their API
        # Converts their response to our SearchResult
```

**Why Adapters?**
1. **Isolation:** Copilot changes don't break our code
2. **Translation:** Convert between our interfaces and theirs
3. **Fallback Logic:** Handle failures gracefully
4. **Feature Flags:** Easy to enable/disable
5. **Testing:** Can mock adapters for testing

---

### `/src/copilot_backend/` - Forked Copilot (Git Submodule)

**Purpose:** The forked ComfyUI-Copilot code, managed as a git submodule.

**What we KEEP:**
- `backend/service/` - Validation and repair agents
- `backend/utils/modelscope_gateway.py` - ModelScope search
- `backend/utils/comfy_gateway.py` - ComfyUI API interface
- `backend/dao/` - SQL state management (optional)

**What we REMOVE (via pruning script):**
- `ui/` - All frontend code
- `public/` - Web assets
- `index.html` - Web interface
- `locales/` - Internationalization
- `dist/` - Built frontend
- `entry/` - ComfyUI plugin entry points

**Management:**
```bash
# Initial setup
git submodule add https://github.com/AIDC-AI/ComfyUI-Copilot src/copilot_backend

# Update from upstream
cd src/copilot_backend
git pull origin main

# Our pruning script removes unnecessary files
./scripts/prune_copilot.sh
```

---

## Configuration Structure

### `/config/default.toml`
```toml
[core]
# Our core features - always available
workflow_dirs = ["workflows/"]
output_dir = "output/"

[adapters]
# Which adapters to enable
enable_validation = false    # Off by default
enable_modelscope = false   # Off by default
enable_sql_state = false    # Off by default
enable_auto_repair = false  # Off by default

[search]
# Search backend priority
backends = ["civitai", "modelscope", "huggingface"]
```

---

## How Files Work Together

### Example: Processing a Workflow

```
User runs: comfywatchman analyze workflow.json

1. cli.py (unchanged)
   ↓ Calls
2. core.py (unchanged)
   ↓ Calls
3. scanner.py (unchanged) - Extracts models
   ↓
4. search.py (enhanced) - Tries search backends
   ├→ CivitaiSearch (our code)
   └→ ModelScopeAdapter → copilot_backend (if enabled)
   ↓
5. ValidationAdapter (if enabled)
   └→ copilot_backend/debug_agent.py
   ↓
6. download.py (unchanged) - Generates scripts
   ↓
7. Output generated
```

**Key Point:** If Copilot isn't available or enabled, flow works exactly as today (steps 4-5 just skip Copilot parts).

---

## Dependency Management

### Main Package (`pyproject.toml`)
```toml
[project]
dependencies = [
    # Our core dependencies only
    "requests>=2.25.0",
    "click>=8.0.0",
    "toml>=0.10.0"
]

[project.optional-dependencies]
# Install with: pip install comfywatchman[copilot]
copilot = [
    "sqlalchemy>=1.4.0,<2.0",
    "openai-agents>=0.3.0",
    "modelscope>=1.28.0"
]

# Install with: pip install comfywatchman[dev]
dev = [
    "pytest>=6.0.0",
    "black>=22.0.0",
    "mypy>=0.900"
]
```

---

## State Management Options

### Default: JSON Files (Our Current Approach)
```
state/
├── download_state.json       # Download tracking
├── search_cache/             # Search result cache
│   └── model_name.json      # Cached results
└── found_models_cache.json  # Inventory cache
```

### Optional: SQL Database (From Copilot)
```
state/
└── comfywatchman.db          # SQLite database
    ├── workflows table       # Workflow versions
    ├── validations table     # Validation history
    └── repairs table         # Repair history
```

**User chooses via config:**
```toml
[state]
backend = "json"  # or "sql"
```

---

## Testing Structure

### Unit Tests
- Test our core functions (unchanged)
- Test adapters in isolation (with mocks)
- Test feature flag system

### Integration Tests
- Test with Copilot available
- Test with Copilot unavailable
- Test fallback scenarios
- Test each adapter

### Test Matrix
```
Run tests with:
1. No Copilot dependencies installed
2. Copilot installed but disabled
3. Copilot installed and enabled
4. Partial features enabled
```

---

## Benefits of This Structure

### 1. **Clean Separation**
- Our code is in `comfywatchman/`
- Integration is in `adapters/`
- Their code is in `copilot_backend/`
- Clear boundaries, no mixing

### 2. **Gradual Integration**
- Can add one adapter at a time
- Each feature independently testable
- Easy rollback if issues

### 3. **User Control**
- Install only what you need
- Enable only what you want
- Configure everything

### 4. **Maintainability**
- Copilot updates don't break our code
- Can update submodule independently
- Adapters isolate changes

### 5. **Testing**
- Can test with/without Copilot
- Mock adapters for unit tests
- Real integration tests

### 6. **Documentation**
- Clear structure makes it obvious where things are
- Adapters are self-documenting interfaces
- Config examples show all options

---

## Migration Path

### From Current Structure to Future:

1. **Create `adapters/` directory**
2. **Fork Copilot as submodule**
3. **Write first adapter (ModelScope search)**
4. **Update config system**
5. **Test with/without Copilot**
6. **Add more adapters incrementally**

**No breaking changes** - Everything continues to work during migration.

---

## Summary

This file tree architecture achieves:
- ✅ **Our tool works standalone** (no Copilot required)
- ✅ **Clean integration** (via adapters)
- ✅ **User control** (config flags)
- ✅ **Easy maintenance** (clear boundaries)
- ✅ **Gradual adoption** (one feature at a time)
- ✅ **Fallback safety** (graceful degradation)

The key insight: **Adapters are the bridge** that let us take the best of both worlds without coupling or dependencies.