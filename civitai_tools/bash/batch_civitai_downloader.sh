#!/bin/bash

# Civitai Batch Downloader
# Batch processes multiple model downloads:
# - Accepts file input or command-line arguments
# - Retry logic: 3 attempts with exponential backoff
# - Logs failures to failed_downloads.txt for review
# - Progress tracking throughout batch

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
DOWNLOADER_SCRIPT="civitai_tools/bash/civitai_url_downloader.sh"
INPUT_FILE=""
FAILED_LOG="failed_downloads.txt"
MAX_RETRIES=3
RETRY_DELAY_BASE=10  # Base delay in seconds (will be multiplied by retry attempt for exponential backoff)
TEMP_DIR="/tmp/civitai_batch_downloader_$$"
mkdir -p "$TEMP_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to show usage
show_usage() {
    echo "Usage: $0 [input_file_or_ids...]"
    echo ""
    echo "Input can be:"
    echo "  - A file path containing URLs/IDs (one per line)"
    echo "  - Direct model IDs or URLs as arguments"
    echo ""
    echo "Examples:"
    echo "  $0 models_to_download.txt"
    echo "  $0 1091495 670378 \"https://civitai.com/models/123456\""
    exit 1
}

# Parse command line arguments
if [[ $# -eq 0 ]]; then
    show_usage
elif [[ $# -eq 1 ]] && [[ -f "$1" ]]; then
    INPUT_FILE="$1"
else
    # Arguments are direct model IDs or URLs
    INPUT_MODE="args"
    DIRECT_ARGS=("$@")
fi

# Function to extract model ID from various inputs
extract_model_id() {
    local input="$1"
    
    # Match both https://civitai.com/models/{id} and https://civitai.com/models/{id}/{name}
    if [[ "$input" =~ ^https://civitai\.com/models/([0-9]+)(/.*)?$ ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    elif [[ "$input" =~ ^[0-9]+$ ]]; then
        # Input is already a numeric ID
        echo "$input"
        return 0
    else
        return 1
    fi
}

# Function to download with retry logic
download_with_retry() {
    local model_ref="$1"
    local attempt=1
    
    while [[ $attempt -le $MAX_RETRIES ]]; do
        log_info "Attempt $attempt/$MAX_RETRIES: Downloading $model_ref"
        
        # Extract ID for the downloader script
        local model_id
        model_id=$(extract_model_id "$model_ref") || { log_error "Invalid model reference: $model_ref"; return 1; }
        
        if "$DOWNLOADER_SCRIPT" "$model_id"; then
            log_success "Successfully downloaded: $model_ref"
            return 0
        else
            log_error "Download failed (attempt $attempt): $model_ref"
            
            if [[ $attempt -lt $MAX_RETRIES ]]; then
                local delay
                delay=$((RETRY_DELAY_BASE * attempt))  # Exponential backoff
                log_info "Waiting $delay seconds before retry..."
                sleep "$delay"
            fi
        fi
        
        ((attempt++))
    done
    
    log_error "Failed to download after $MAX_RETRIES attempts: $model_ref"
    return 1
}

# Initialize failed log
if [[ -f "$FAILED_LOG" ]]; then
    log_info "Clearing previous failed log: $FAILED_LOG"
    > "$FAILED_LOG"
else
    touch "$FAILED_LOG"
fi

log_info "Starting batch download process"

# Prepare download list
DOWNLOAD_LIST="$TEMP_DIR/download_list.txt"
> "$DOWNLOAD_LIST"

if [[ "$INPUT_MODE" == "args" ]]; then
    # Process command-line arguments
    for arg in "${DIRECT_ARGS[@]}"; do
        # Skip comments and empty lines
        if [[ "$arg" =~ ^[[:space:]]*# ]] || [[ -z "$arg" ]]; then
            continue
        fi
        echo "$arg" >> "$DOWNLOAD_LIST"
    done
else
    # Process input file
    if [[ ! -f "$INPUT_FILE" ]]; then
        log_error "Input file does not exist: $INPUT_FILE"
        exit 1
    fi
    
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
            continue
        fi
        echo "$line" >> "$DOWNLOAD_LIST"
    done < "$INPUT_FILE"
fi

# Get total count for progress tracking
TOTAL_COUNT=$(wc -l < "$DOWNLOAD_LIST")
if [[ "$TOTAL_COUNT" =~ ^[0-9]+$ ]]; then
    TOTAL_COUNT=$((TOTAL_COUNT))
else
    TOTAL_COUNT=0
fi

log_info "Processing $TOTAL_COUNT items from input"

# Process each item in the download list
SUCCESS_COUNT=0
FAIL_COUNT=0
CURRENT_ITEM=0

while IFS= read -r model_ref; do
    # Skip empty lines
    if [[ -z "$model_ref" ]]; then
        continue
    fi
    
    ((CURRENT_ITEM++))
    log_info "Processing item $CURRENT_ITEM/$TOTAL_COUNT: $model_ref"
    
    if download_with_retry "$model_ref"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
        # Log failure to file
        echo "$model_ref" >> "$FAILED_LOG"
    fi
    
    # Show progress
    log_info "Progress: $SUCCESS_COUNT successful, $FAIL_COUNT failed out of $TOTAL_COUNT total"
    echo
done < "$DOWNLOAD_LIST"

# Summary
echo "========================================="
log_info "BATCH DOWNLOAD SUMMARY"
echo "========================================="
log_info "Total items processed: $TOTAL_COUNT"
log_info "Successful downloads: $SUCCESS_COUNT"
log_info "Failed downloads: $FAIL_COUNT"

if [[ $FAIL_COUNT -gt 0 ]]; then
    log_warning "Some downloads failed. Check $FAILED_LOG for details:"
    cat "$FAILED_LOG"
fi

if [[ $SUCCESS_COUNT -eq $TOTAL_COUNT ]]; then
    log_success "All downloads completed successfully!"
else
    log_error "Some downloads failed. See $FAILED_LOG for failed items."
fi

# Clean up
rm -rf "$TEMP_DIR"

echo "========================================="