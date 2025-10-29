#!/bin/bash

# Civitai Search Debugger
# Shows exact API queries, raw responses, scoring breakdowns
# and suggests alternative approaches when search fails

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
API_BASE_URL="https://civitai.com/api/v1"
CIVITAI_API_KEY="${CIVITAI_API_KEY:-}"

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
    echo "Usage: $0 <search_term> [OPTIONS]"
    echo "Options:"
    echo "  --type TYPE     Model type (LORA, Checkpoint, etc.) [default: LORA]"
    echo "  --nsfw BOOLEAN  Include NSFW results (true/false) [default: true]"
    echo ""
    echo "Example: $0 \"Better detailed pussy and anus\" --type LORA"
    exit 1
}

# Parse command line arguments
SEARCH_TERM=""
MODEL_TYPE="LORA"
NSFW="true"

while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            MODEL_TYPE="$2"
            shift 2
            ;;
        --nsfw)
            NSFW="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            if [[ -z "$SEARCH_TERM" ]]; then
                SEARCH_TERM="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$SEARCH_TERM" ]]; then
    log_error "Search term is required"
    show_usage
fi

log_info "Civitai Search Debugger"
log_info "Search Term: \"$SEARCH_TERM\""
log_info "Model Type: $MODEL_TYPE"
log_info "NSFW: $NSFW"
echo

# Function to perform API request and return result
perform_api_request() {
    local query="$1"
    local nsfw_param="$2"
    local type_param="$3"
    local api_url="${API_BASE_URL}/models?query=${query}&types=${type_param}&limit=10&sort=Highest%20Rated"
    
    if [[ "$nsfw_param" == "true" ]]; then
        api_url="${api_url}&nsfw=true"
    fi
    
    log_info "API URL: $api_url"
    
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
    
    echo "$http_code"
    echo "$body"
}

# Encode query parameter
encode_query() {
    local query="$1"
    # URL encode the query (basic version - could be enhanced)
    echo "$query" | sed 's/ /%20/g' | sed 's/&/%26/g' | sed 's/+/%2B/g'
}

ENCODED_QUERY=$(encode_query "$SEARCH_TERM")

echo "=== Query Search (nsfw=$NSFW) ==="
QUERY_HTTP_CODE=$(perform_api_request "$ENCODED_QUERY" "$NSFW" "$MODEL_TYPE")
QUERY_BODY=$(echo "$QUERY_HTTP_CODE" | sed -n '$p')
QUERY_HTTP_CODE=$(echo "$QUERY_HTTP_CODE" | sed -n '1p')

log_info "Response: $QUERY_HTTP_CODE"
if [[ "$QUERY_HTTP_CODE" -eq 200 ]]; then
    log_info "Items Returned: $(echo "$QUERY_BODY" | jq -r '.items | length' 2>/dev/null || echo "0")"
    
    # Show top candidates
    local candidate_count
    candidate_count=$(echo "$QUERY_BODY" | jq -r '.items | length' 2>/dev/null || echo "0")
    if [[ "$candidate_count" -gt 0 ]]; then
        log_info "Top candidates:"
        for i in $(seq 0 $((candidate_count < 5 ? candidate_count - 1 : 4))); do
            if [[ $i -eq 0 ]]; then
                echo -n "  [1] "
            else
                echo -n "  [$((i+1))] "
            fi
            
            local candidate_id
            candidate_id=$(echo "$QUERY_BODY" | jq -r ".items[$i].id" 2>/dev/null || echo "N/A")
            local candidate_name
            candidate_name=$(echo "$QUERY_BODY" | jq -r ".items[$i].name" 2>/dev/null || echo "N/A")
            local candidate_type
            candidate_type=$(echo "$QUERY_BODY" | jq -r ".items[$i].type" 2>/dev/null || echo "N/A")
            
            echo "ID: $candidate_id | Name: \"$candidate_name\" | Type: $candidate_type"
        done
    fi
else
    log_error "Request failed with HTTP code: $QUERY_HTTP_CODE"
fi
echo

# Try without NSFW flag if initial search failed
if [[ "$QUERY_HTTP_CODE" -ne 200 ]] || [[ "$(echo "$QUERY_BODY" | jq -r '.items | length' 2>/dev/null || echo "0")" -eq 0 ]]; then
    echo "=== Query Search (without NSFW flag) ==="
    QUERY_HTTP_CODE_NO_NSFW=$(perform_api_request "$ENCODED_QUERY" "false" "$MODEL_TYPE")
    QUERY_BODY_NO_NSFW=$(echo "$QUERY_HTTP_CODE_NO_NSFW" | sed -n '$p')
    QUERY_HTTP_CODE_NO_NSFW=$(echo "$QUERY_HTTP_CODE_NO_NSFW" | sed -n '1p')
    
    log_info "Response: $QUERY_HTTP_CODE_NO_NSFW"
    if [[ "$QUERY_HTTP_CODE_NO_NSFW" -eq 200 ]]; then
        log_info "Items Returned: $(echo "$QUERY_BODY_NO_NSFW" | jq -r '.items | length' 2>/dev/null || echo "0")"
    else
        log_error "Request failed with HTTP code: $QUERY_HTTP_CODE_NO_NSFW"
    fi
    echo
fi

# Tag-based search
echo "=== Tag-based Search ==="
log_info "Extracting tags from search term: $SEARCH_TERM"

# Simple tag extraction
TAGS=()
IFS=' ' read -ra TERMS <<< "$SEARCH_TERM"

# Common tags for NSFW model search
ANATOMICAL_TAGS=("anatomy" "anatomical" "detail" "details" "eyes" "pussy" "anus" "breasts" "ass" "thighs")
STYLE_TAGS=("realistic" "high" "definition" "hd" "detailed" "detail")
CONTENT_TAGS=("nsfw" "explicit" "nude" "naked" "adult")

# Extract tags from search terms
for term in "${TERMS[@]}"; do
    term_lower=$(echo "$term" | tr '[:upper:]' '[:lower:]')
    # Skip common words
    if [[ "$term_lower" =~ ^(and|the|for|with|v[0-9]*|xl)$ ]]; then
        continue
    fi
    
    # Add if it's a known tag
    for tag in "${ANATOMICAL_TAGS[@]}" "${STYLE_TAGS[@]}" "${CONTENT_TAGS[@]}"; do
        if [[ "$term_lower" == "$tag" ]]; then
            TAGS+=("$tag")
            break
        fi
    done
    
    # Add if it's a meaningful word (longer than 2 chars)
    if [[ ${#term} -gt 2 ]]; then
        TAGS+=("$term")
    fi
done

# Remove duplicates
UNIQUE_TAGS=()
for tag in "${TAGS[@]}"; do
    # Check if tag is already in UNIQUE_TAGS
    found=0
    for unique_tag in "${UNIQUE_TAGS[@]}"; do
        if [[ "$tag" == "$unique_tag" ]]; then
            found=1
            break
        fi
    done
    if [[ $found -eq 0 ]]; then
        UNIQUE_TAGS+=("$tag")
    fi
done

# Search with each tag
for tag in "${UNIQUE_TAGS[@]}"; do
    log_info "Trying tag: $tag"
    local tag_url="${API_BASE_URL}/models?tag=${tag}&types=${MODEL_TYPE}&nsfw=true&limit=5"
    
    log_info "API URL: $tag_url"
    
    local headers=()
    if [[ -n "$CIVITAI_API_KEY" ]]; then
        headers+=("-H" "Authorization: Bearer $CIVITAI_API_KEY")
    fi
    
    local tag_response
    tag_response=$(curl -s -w "\n%{http_code}" "${headers[@]}" "$tag_url" || true)
    local tag_http_code
    tag_http_code=$(echo "$tag_response" | tail -n1)
    local tag_body
    tag_body=$(echo "$tag_response" | head -n -1)
    
    log_info "Response: $tag_http_code"
    if [[ "$tag_http_code" -eq 200 ]]; then
        local tag_items
        tag_items=$(echo "$tag_body" | jq -r '.items | length' 2>/dev/null || echo "0")
        log_info "Items Returned: $tag_items"
        
        if [[ "$tag_items" -gt 0 ]]; then
            log_info "First candidate with tag '$tag':"
            local first_id
            first_id=$(echo "$tag_body" | jq -r ".items[0].id" 2>/dev/null || echo "N/A")
            local first_name
            first_name=$(echo "$tag_body" | jq -r ".items[0].name" 2>/dev/null || echo "N/A")
            echo "  ID: $first_id | Name: \"$first_name\""
        fi
    else
        log_error "Request failed with HTTP code: $tag_http_code"
    fi
    echo
done

# Diagnosis and suggestions
echo "=== DIAGNOSIS ==="

if [[ "$QUERY_HTTP_CODE" -eq 200 ]]; then
    local items_count
    items_count=$(echo "$QUERY_BODY" | jq -r '.items | length' 2>/dev/null || echo "0")
    if [[ "$items_count" -eq 0 ]]; then
        log_warning "[DIAGNOSIS] Query search returned 0 results - likely term filtering"
    elif [[ "$items_count" -gt 0 ]]; then
        # Check if the results match our search terms
        local found_match=0
        for i in $(seq 0 $((items_count - 1))); do
            local item_name
            item_name=$(echo "$QUERY_BODY" | jq -r ".items[$i].name" 2>/dev/null || echo "")
            if [[ "$item_name" != "null" ]] && [[ -n "$item_name" ]]; then
                # Check if search term appears in item name (case-insensitive)
                if [[ $(echo "$item_name" | grep -i -o "$SEARCH_TERM" | head -n 1) ]]; then
                    found_match=1
                    break
                fi
            fi
        done
        
        if [[ $found_match -eq 0 ]]; then
            log_warning "[DIAGNOSIS] Query search found results but none match search terms exactly"
        else
            log_success "[DIAGNOSIS] Found potentially matching results"
        fi
    fi
else
    log_error "[DIAGNOSIS] API request failed - check your connection and API key"
fi

echo
echo "=== SUGGESTIONS ==="
if [[ "$QUERY_HTTP_CODE" -ne 200 ]] || [[ "$(echo "$QUERY_BODY" | jq -r '.items | length' 2>/dev/null || echo "0")" -eq 0 ]]; then
    log_info "[SUGGESTION] Try direct ID lookup if model URL known"
    log_info "[SUGGESTION] Try tag search: anatomy, detail, nsfw"
fi

if [[ ${#UNIQUE_TAGS[@]} -gt 0 ]]; then
    log_info "[SUGGESTION] Try combining these tags: ${UNIQUE_TAGS[*]}"
fi

log_info "[SUGGESTION] Check for alternative names or creators"
log_info "[SUGGESTION] Try the Civitai advanced search script for multi-strategy search"