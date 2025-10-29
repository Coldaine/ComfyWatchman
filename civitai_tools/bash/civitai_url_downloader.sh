#!/bin/bash

# Civitai Direct ID Downloader
# Extracts model ID from Civitai URLs or uses direct model ID
# Fetches model details via /api/v1/models/{id} endpoint
# Downloads specified version (default: latest) with SHA256 verification

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
API_BASE_URL="https://civitai.com/api/v1"
DOWNLOAD_DIR="${CIVITAI_DOWNLOAD_DIR:-./downloads}"
CIVITAI_API_KEY="${CIVITAI_API_KEY:-}"
TEMP_DIR="/tmp/civitai_downloader_$$"
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

# Function to extract model ID from URL
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

# Function to fetch model details by ID
fetch_model_details() {
    local model_id="$1"
    local api_url="${API_BASE_URL}/models/${model_id}"
    
    log_info "Fetching model details for ID: ${model_id}"
    
    local headers=()
    if [[ -n "$CIVITAI_API_KEY" ]]; then
        headers+=("-H" "Authorization: Bearer $CIVITAI_API_KEY")
    fi
    
    local response
    response=$(curl -s -w "\n%{http_code}" "${headers[@]}" "$api_url" || true)
    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" -ne 200 ]]; then
        log_error "Failed to fetch model details: HTTP ${http_code}"
        log_error "Response: $body"
        return 1
    fi
    
    echo "$body"
}

# Function to get download URL from model details
get_download_url() {
    local model_json="$1"
    local version_id="${2:-}"
    
    if [[ -z "$version_id" ]]; then
        # Use latest version
        local latest_version_idx
        latest_version_idx=$(echo "$model_json" | jq -r '.modelVersions | length - 1')
        version_id=$(echo "$model_json" | jq -r ".modelVersions[$latest_version_idx].id")
        log_info "Using latest version ID: $version_id"
    else
        log_info "Using specified version ID: $version_id"
    fi
    
    # Find the download URL for the specified version
    local download_url
    download_url=$(echo "$model_json" | jq -r --arg v_id "$version_id" '
        .modelVersions[] | 
        select(.id == ($v_id | tonumber)) |
        .files[]? |
        select(.primary == true or .sizeKB > 0) |  # Prefer primary file or any file with size
        .downloadUrl
    ' | head -n 1)
    
    if [[ "$download_url" == "null" ]] || [[ -z "$download_url" ]]; then
        # If no primary file found, just get the first available download URL
        download_url=$(echo "$model_json" | jq -r --arg v_id "$version_id" '
            .modelVersions[] | 
            select(.id == ($v_id | tonumber)) |
            .files[]? |
            .downloadUrl
        ' | head -n 1)
    fi
    
    if [[ "$download_url" != "null" ]] && [[ -n "$download_url" ]]; then
        echo "$download_url"
        return 0
    else
        return 1
    fi
}

# Function to download a file with progress and verification
download_file() {
    local download_url="$1"
    local filename="$2"
    
    log_info "Downloading to: $filename"
    
    local headers=()
    if [[ -n "$CIVITAI_API_KEY" ]]; then
        headers+=("-H" "Authorization: Bearer $CIVITAI_API_KEY")
    fi
    
    # Download the file
    curl -L "${headers[@]}" -o "$filename" --progress-bar "$download_url"
    
    if [[ $? -ne 0 ]]; then
        log_error "Download failed for: $download_url"
        return 1
    fi
    
    log_success "Download completed: $filename"
}

# Function to calculate SHA256 hash
calculate_sha256() {
    local filepath="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$filepath" | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$filepath" | cut -d' ' -f1
    else
        log_error "No SHA256 utility found (sha256sum or shasum required)"
        return 1
    fi
}

# Function to verify downloaded file against expected hash
verify_file() {
    local filepath="$1"
    local expected_hash="$2"
    
    log_info "Verifying file integrity..."
    
    local actual_hash
    actual_hash=$(calculate_sha256 "$filepath")
    
    if [[ "$actual_hash" == "$expected_hash" ]]; then
        log_success "SHA256 verification passed"
        return 0
    else
        log_error "SHA256 verification failed"
        log_error "Expected: $expected_hash"
        log_error "Actual: $actual_hash"
        return 1
    fi
}

# Function to get file info from model JSON
get_file_info() {
    local model_json="$1"
    local version_id="${2:-}"
    
    if [[ -z "$version_id" ]]; then
        local latest_version_idx
        latest_version_idx=$(echo "$model_json" | jq -r '.modelVersions | length - 1')
        version_id=$(echo "$model_json" | jq -r ".modelVersions[$latest_version_idx].id")
    fi
    
    # Get the primary file info for the version (or first file if no primary)
    echo "$model_json" | jq -r --arg v_id "$version_id" '
        .modelVersions[] | 
        select(.id == ($v_id | tonumber)) |
        .files[]? |
        select(.primary == true or .sizeKB > 0) |
        {
            name: .name,
            sizeKB: .sizeKB,
            hash: .hashes.SHA256 // empty
        } | @base64'
}

# Main function
main() {
    local input="$1"
    local specified_version_id="${2:-}"
    
    if [[ -z "$input" ]]; then
        log_error "Usage: $0 <model_id_or_url> [version_id]"
        log_error "Example: $0 1091495"
        log_error "Example: $0 \"https://civitai.com/models/1091495\""
        log_error "Example: $0 1091495 9857"
        exit 1
    fi
    
    # Extract model ID
    local model_id
    model_id=$(extract_model_id "$input")
    if [[ $? -ne 0 ]]; then
        log_error "Invalid input. Provide either a Civitai model ID or URL."
        exit 1
    fi
    
    log_info "Model ID extracted: $model_id"
    
    # Create download directory if it doesn't exist
    mkdir -p "$DOWNLOAD_DIR"
    
    # Fetch model details
    local model_details
    model_details=$(fetch_model_details "$model_id")
    if [[ $? -ne 0 ]]; then
        log_error "Failed to fetch model details"
        exit 1
    fi
    
    # Display model info
    local model_name
    model_name=$(echo "$model_details" | jq -r '.name // "Unknown"')
    log_info "Model Name: $model_name"
    
    # Get file information
    local file_info_b64
    file_info_b64=$(get_file_info "$model_details" "$specified_version_id")
    
    if [[ -z "$file_info_b64" ]]; then
        log_error "No downloadable file found for the specified version"
        exit 1
    fi
    
    # Decode file info
    local file_info
    file_info=$(echo "$file_info_b64" | base64 -d)
    local filename
    filename=$(echo "$file_info" | jq -r '.name')
    local expected_hash
    expected_hash=$(echo "$file_info" | jq -r '.hash // empty')
    local size_kb
    size_kb=$(echo "$file_info" | jq -r '.sizeKB // "Unknown"')
    
    log_info "File Name: $filename"
    if [[ "$size_kb" != "Unknown" ]]; then
        log_info "File Size: $((size_kb / 1024)) MB"
    fi
    
    # Get download URL
    local download_url
    download_url=$(get_download_url "$model_details" "$specified_version_id")
    if [[ $? -ne 0 ]]; then
        log_error "No download URL found for the specified version"
        exit 1
    fi
    
    # Prepare final download path
    local final_path
    final_path="$DOWNLOAD_DIR/$filename"
    
    # Download the file
    download_file "$download_url" "$final_path"
    if [[ $? -ne 0 ]]; then
        log_error "Download failed"
        exit 1
    fi
    
    # Verify the download if hash is available
    if [[ -n "$expected_hash" ]]; then
        verify_file "$final_path" "$expected_hash"
        if [[ $? -ne 0 ]]; then
            log_error "Verification failed. Downloaded file may be corrupted."
            exit 1
        else
            log_success "File downloaded and verified successfully: $final_path"
        fi
    else
        log_warning "No hash available for verification. Downloaded to: $final_path"
    fi
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    log_success "Download completed successfully!"
}

# Run main function with arguments
main "$@"