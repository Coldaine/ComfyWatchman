#!/bin/bash
# ComfyFixerSmart Compatibility Shell Wrapper
#
# Provides shell-level compatibility for ComfyFixerSmart migration.
# Automatically detects and uses the best available system.

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Add src to PYTHONPATH for new system
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Configuration
COMPATIBILITY_MODE="${COMFYFIXER_COMPATIBILITY_MODE:-auto}"
QUIET_MODE="${COMFYFIXER_QUIET:-false}"

# Logging function
log() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo "$@" >&2
    fi
}

# Error function
error() {
    echo "❌ $@" >&2
}

# Check if new system is available
check_new_system() {
    if python3 -c "from comfywatchman.config import config; from comfywatchman.cli import create_parser" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if legacy system is available
check_legacy_system() {
    if [[ -f "$PROJECT_ROOT/legacy/comfy_fixer.py" ]]; then
        return 0
    else
        return 1
    fi
}

# Show migration prompt
show_migration_prompt() {
    # Only show if not suppressed and it's been a while
    local state_file="$PROJECT_ROOT/config/.compatibility_state.json"
    local current_time=$(date +%s)
    local last_prompt=0

    if [[ -f "$state_file" ]]; then
        last_prompt=$(python3 -c "import json, sys; data=json.load(open('$state_file')); print(data.get('last_migration_prompt', 0))" 2>/dev/null || echo "0")
    fi

    local days_since=$(( (current_time - last_prompt) / 86400 ))

    if [[ $days_since -ge 7 ]]; then
        cat >&2 << 'EOF'

================================================================================
🚀 COMFYFIXERSMART MIGRATION AVAILABLE
================================================================================
A new, improved version of ComfyFixerSmart is available with:
  • 2-3x faster processing
  • Better error handling and recovery
  • Enhanced state management
  • More CLI options
  • Comprehensive validation tools

To migrate:
  1. python3 scripts/migrate_config.py
  2. python3 scripts/migrate_state.py --backup
  3. python3 scripts/validate_migration.py
  4. Use: python3 -m comfywatchman.cli

Documentation: docs/migration-guide.md
Cheat sheet: docs/migration-cheat-sheet.md

To disable this prompt: export COMFYFIXER_QUIET=true
================================================================================

EOF

        # Update last prompt time
        mkdir -p "$PROJECT_ROOT/config"
        python3 -c "
import json, os
state_file = '$state_file'
data = {}
if os.path.exists(state_file):
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
    except:
        pass
data['last_migration_prompt'] = $current_time
with open(state_file, 'w') as f:
    json.dump(data, f, indent=2)
        " 2>/dev/null || true
    fi
}

# Translate legacy arguments to new system
translate_args() {
    local new_args=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                new_args+=("--help")
                ;;
            --verify-urls)
                new_args+=("--verify-urls")
                ;;
            --dry-run)
                new_args+=("--no-script")
                ;;
            -*)
                # Pass through other options
                new_args+=("$1")
                ;;
            *)
                # Positional arguments
                new_args+=("$1")
                ;;
        esac
        shift
    done

    echo "${new_args[@]}"
}

# Main logic
main() {
    local use_new_system=false

    case "$COMPATIBILITY_MODE" in
        new)
            use_new_system=true
            ;;
        legacy)
            use_new_system=false
            ;;
        auto)
            if check_new_system; then
                use_new_system=true
            else
                use_new_system=false
            fi
            ;;
        *)
            if check_new_system; then
                use_new_system=true
            else
                use_new_system=false
            fi
            ;;
    esac

    if $use_new_system && check_new_system; then
        log "🔄 Using new ComfyFixerSmart system"

        # Translate arguments
        local translated_args
        translated_args=$(translate_args "$@")

        # Run new system
        exec python3 -m comfywatchman.cli $translated_args

    elif check_legacy_system; then
        log "🔄 Using legacy ComfyFixerSmart system"

        # Show migration prompt if new system is available
        if check_new_system; then
            show_migration_prompt
        fi

        # Run legacy system
        exec python3 "$PROJECT_ROOT/legacy/comfy_fixer.py" "$@"

    else
        error "No ComfyFixerSmart system available!"
        error "Please check your installation."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"