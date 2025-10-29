#!/bin/bash

# Civitai Fuzzy Model Finder
# Interactive tool for when automated search fails:
# - Keyword decomposition (searches each word separately)
# - Browsing popular models in relevant categories
# - Presents top 5 candidates with details
# - User selects correct model

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
API_BASE_URL="https://civitai.com/api/v1"
CIVITAI_API_KEY="${CIVITAI_API_KEY:-}"
DOWNLOADER_SCRIPT="civitai_tools/bash/civitai_url_downloader.sh"
TEMP_DIR="/tmp/civitai_fuzzy_finder_$$"
mkdir -p "$TEMP_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_highlight() { echo -e "${PURPLE}[HIGHLIGHT]${NC} $1"; }

# Function to show usage
show_usage() {
    echo "Usage: $0 [search_term]"
    echo ""
    echo "Example: $0 \"Better detailed pussy and anus\""
    echo "If no search term provided, you will be prompted."
    exit 1
}

# Parse command line arguments
SEARCH_TERM="$1"

if [[ -z "$SEARCH_TERM" ]]; then
    echo -e "${BLUE}=== Fuzzy Model Finder ===${NC}"
    read -p "Enter search term: " SEARCH_TERM
    if [[ -z "$SEARCH_TERM" ]]; then
        log_error "Search term is required"
        show_usage
    fi
fi

# Function to encode query parameter
encode_query() {
    local query="$1"
    # URL encode the query (basic version - could be enhanced)
    echo "$query" | sed 's/ /%20/g' | sed 's/&/%26/g' | sed 's/+/%2B/g' | sed 's/(/%28/g' | sed 's/)/%29/g'
}

# Function to calculate match score
calculate_score() {
    local item_name="$1"
    local search_term="$2"
    
    local score=0
    
    # Case-insensitive matching
    local item_lower=$(echo "$item_name" | tr '[:upper:]' '[:lower:]')
    local search_lower=$(echo "$search_term" | tr '[:upper:]' '[:lower:]')
    
    # Exact name match: +150
    if [[ "$item_lower" == "$search_lower" ]]; then
        score=$((score + 150))
    fi
    
    # Partial name match: +75
    if [[ "$item_lower" =~ .*"$search_lower".* ]] || [[ "$search_lower" =~ .*"$item_lower".* ]]; then
        score=$((score + 75))
    fi
    
    # Keyword matches: +25 per keyword
    local keywords
    read -ra keywords <<< "$search_term"
    for keyword in "${keywords[@]}"; do
        local keyword_lower=$(echo "$keyword" | tr '[:upper:]' '[:lower:]')
        if [[ ${#keyword_lower} -gt 2 ]] && [[ "$item_lower" =~ .*"$keyword_lower".* ]]; then
            score=$((score + 25))
        fi
    done
    
    # Common tags that indicate relevance
    local relevant_tags=("anatomy" "anatomical" "detail" "details" "hd" "definition" "high" "realistic" "nsfw" "explicit")
    for tag in "${relevant_tags[@]}"; do
        if [[ "$item_lower" =~ .*"$tag".* ]]; then
            score=$((score + 15))
        fi
    done
    
    # Bonus for model-like extensions in name (indicates it's likely a model)
    if [[ "$item_lower" =~ .*"(lora|checkpoint|vae)".* ]]; then
        score=$((score + 10))
    fi
    
    echo "$score"
}

# Function to perform keyword search
perform_keyword_search() {
    local keyword="$1"
    local api_url="${API_BASE_URL}/models?query=${keyword}&limit=5&nsfw=true"
    
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
    
    if [[ "$http_code" -eq 200 ]]; then
        echo "$body"
        return 0
    else
        return 1
    fi
}

# Function to get popular models in a category
browse_popular_models() {
    local tag="$1"
    local api_url="${API_BASE_URL}/models?tag=${tag}&limit=10&nsfw=true&sort=Most%20Downloaded"
    
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
    
    if [[ "$http_code" -eq 200 ]]; then
        echo "$body"
        return 0
    else
        return 1
    fi
}

# Function to download a model by ID
download_model_by_id() {
    local model_id="$1"
    local version_id="${2:-}"
    
    if [[ -f "$DOWNLOADER_SCRIPT" ]]; then
        if [[ -n "$version_id" ]]; then
            "$DOWNLOADER_SCRIPT" "$model_id" "$version_id"
        else
            "$DOWNLOADER_SCRIPT" "$model_id"
        fi
    else
        log_error "Downloader script not found: $DOWNLOADER_SCRIPT"
        log_info "Model download URL: https://civitai.com/api/download/models/$model_id"
        return 1
    fi
}

log_info "Starting fuzzy search for: \"$SEARCH_TERM\""

echo -e "${BLUE}=== Fuzzy Model Finder ===${NC}"
echo -e "${BLUE}Search term:${NC} $SEARCH_TERM"
echo

# Step 1: Keyword decomposition search
log_info "Trying keyword searches..."

# Split search term into keywords
local keywords
read -ra keywords <<< "$SEARCH_TERM"

# Track all results
all_results_file="$TEMP_DIR/all_results.jsonl"
> "$all_results_file"

for keyword in "${keywords[@]}"; do
    # Skip common words that won't yield useful results
    if [[ "$keyword" =~ ^(and|the|for|with|a|an|of|in|on|at|to|is|it|be|as|so|or|but|no|can|will|would|should|may|might|must|shall)$ ]]; then
        continue
    fi
    
    # Skip very short words
    if [[ ${#keyword} -lt 3 ]]; then
        continue
    fi
    
    log_info "  Keyword \"$keyword\":"
    
    ENCODED_KEYWORD=$(encode_query "$keyword")
    keyword_result=$(perform_keyword_search "$ENCODED_KEYWORD" || true)
    
    if [[ -n "$keyword_result" ]]; then
        local count
        count=$(echo "$keyword_result" | jq -r '.items | length' 2>/dev/null || echo "0")
        log_info "    Found $count models"
        
        # Process results and add to all_results
        for i in $(seq 0 $((count > 5 ? 4 : count - 1)) 2>/dev/null); do
            if [[ $i -ge $count ]]; then
                break
            fi
            
            local item_id
            item_id=$(echo "$keyword_result" | jq -r ".items[$i].id" 2>/dev/null || echo "null")
            local item_name
            item_name=$(echo "$keyword_result" | jq -r ".items[$i].name" 2>/dev/null || echo "null")
            local item_type
            item_type=$(echo "$keyword_result" | jq -r ".items[$i].type" 2>/dev/null || echo "null")
            
            if [[ "$item_id" != "null" ]] && [[ "$item_name" != "null" ]]; then
                local score
                score=$(calculate_score "$item_name" "$SEARCH_TERM")
                
                # Get download count and rating if available
                local download_count
                download_count=$(echo "$keyword_result" | jq -r ".items[$i].stats.downloadCount" 2>/dev/null || echo "0")
                local rating
                rating=$(echo "$keyword_result" | jq -r ".items[$i].stats.rating.average" 2>/dev/null || echo "0.0")
                
                # Output result in JSON format
                echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"type\": \"$item_type\", \"score\": $score, \"download_count\": $download_count, \"rating\": $rating, \"keyword_source\": \"$keyword\", \"search_method\": \"keyword\" }" >> "$all_results_file"
            fi
        done
    else
        log_warning "    No results for keyword: $keyword"
    fi
done

# Step 2: Browse popular anatomical/detail models if keyword search was limited
log_info "Browsing popular models in relevant categories..."

# Common tags for anatomically detailed models
relevant_tags=("anatomy" "anatomical" "detail" "details" "eyes" "pussy" "anus" "breasts" "ass" "thighs" "nipples")

for tag in "${relevant_tags[@]}"; do
    if [[ "$SEARCH_TERM" =~ .*"$tag".* ]]; then  # Only search tag if our search term contains it
        log_info "  Browsing tag: $tag"
        
        tag_result=$(browse_popular_models "$tag" || true)
        if [[ -n "$tag_result" ]]; then
            local count
            count=$(echo "$tag_result" | jq -r '.items | length' 2>/dev/null || echo "0")
            log_info "    Found $count models"
            
            # Process top results from this category
            for i in $(seq 0 $((count > 3 ? 2 : count - 1)) 2>/dev/null); do
                if [[ $i -ge $count ]]; then
                    break
                fi
                
                local item_id
                item_id=$(echo "$tag_result" | jq -r ".items[$i].id" 2>/dev/null || echo "null")
                local item_name
                item_name=$(echo "$tag_result" | jq -r ".items[$i].name" 2>/dev/null || echo "null")
                local item_type
                item_type=$(echo "$tag_result" | jq -r ".items[$i].type" 2>/dev/null || echo "null")
                
                if [[ "$item_id" != "null" ]] && [[ "$item_name" != "null" ]]; then
                    local score
                    score=$(calculate_score "$item_name" "$SEARCH_TERM")
                    
                    # Get download count and rating
                    local download_count
                    download_count=$(echo "$tag_result" | jq -r ".items[$i].stats.downloadCount" 2>/dev/null || echo "0")
                    local rating
                    rating=$(echo "$tag_result" | jq -r ".items[$i].stats.rating.average" 2>/dev/null || echo "0.0")
                    
                    # Output result in JSON format
                    echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"type\": \"$item_type\", \"score\": $score, \"download_count\": $download_count, \"rating\": $rating, \"tag_source\": \"$tag\", \"search_method\": \"tag\" }" >> "$all_results_file"
                fi
            done
        fi
    fi
done

# Step 3: Combine and rank all results
log_info "Compiling and ranking results..."

if [[ -s "$all_results_file" ]]; then
    # Find top 5 candidates by score
    echo
    log_highlight "Top 5 Candidates:"
    
    candidate_count=0
    while IFS= read -r line; do
        if [[ -n "$line" ]] && [[ $candidate_count -lt 5 ]]; then
            local model_id
            model_id=$(echo "$line" | jq -r '.model_id // "N/A"')
            local name
            name=$(echo "$line" | jq -r '.name // "N/A"')
            local model_type
            model_type=$(echo "$line" | jq -r '.type // "N/A"')
            local score
            score=$(echo "$line" | jq -r '.score // "N/A"')
            local downloads
            downloads=$(echo "$line" | jq -r '.download_count // "N/A"')
            local rating
            rating=$(echo "$line" | jq -r '.rating // "N/A"')
            local source_method
            source_method=$(echo "$line" | jq -r '.search_method // "unknown"')
            
            # Format the output
            if [[ $candidate_count -eq 0 ]]; then
                echo -e "  ${GREEN}[1]${NC} $name (ID: $model_id)"
            else
                echo -e "  [$(($candidate_count+1))] $name (ID: $model_id)"
            fi
            
            echo "      Type: $model_type | Score: $score | Downloads: $downloads | Rating: $rating | Method: $source_method"
            
            # Store in array for later selection
            eval "candidate_$candidate_count=(\"$model_id\" \"$name\" \"$score\")"
            ((candidate_count++))
        fi
    done < <(sort -t':' -k4 -nr "$all_results_file")  # Sort by score field
    
    # Step 4: Interactive selection
    echo
    while true; do
        read -p $'Select model to download (1-5), or [S]earch again, [Q]uit: ' selection
        
        case $selection in
            [1-5])
                if [[ $selection -le $candidate_count ]]; then
                    local idx=$(($selection - 1))
                    local selected_id
                    eval "selected_id=\${candidate_$idx[0]}"
                    local selected_name
                    eval "selected_name=\${candidate_$idx[1]}"
                    
                    echo
                    log_info "Selected: $selected_name (ID: $selected_id)"
                    log_info "Starting download..."
                    
                    download_model_by_id "$selected_id"
                    log_success "Download completed for: $selected_name"
                    break
                else
                    log_warning "Invalid selection. Please choose 1-$candidate_count"
                fi
                ;;
            [Ss])
                # Allow user to search again with new term
                read -p "Enter new search term: " new_search_term
                if [[ -n "$new_search_term" ]]; then
                    # Reset and start over with new term
                    SEARCH_TERM="$new_search_term"
                    > "$all_results_file"  # Clear previous results
                    continue 2  # Continue outer loop with new search
                fi
                ;;
            [Qq])
                log_info "Exiting fuzzy finder."
                break
                ;;
            *)
                log_warning "Invalid option. Please select 1-5, S to search again, or Q to quit."
                ;;
        esac
    done
else
    log_warning "No results found with any strategy"
    echo "Try a different search term or check if the model exists on Civitai directly."
fi

# Clean up
rm -rf "$TEMP_DIR"

echo
log_success "Fuzzy finder completed."