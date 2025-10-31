#!/bin/bash

# Civitai Advanced Multi-Strategy Search
# Implements sophisticated search with cascading fallbacks:
# 1. Query search (multiple parameter combinations)
# 2. Tag-based search (anatomical/detail/NSFW tags)
# 3. Creator-based search (if username known)
# 4. Known models lookup (from known_models.json)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
API_BASE_URL="https://civitai.com/api/v1"
CIVITAI_API_KEY="${CIVITAI_API_KEY:-}"
KNOWN_MODELS_FILE="${KNOWN_MODELS_FILE:-civitai_tools/config/known_models.json}"
TEMP_DIR="/tmp/civitai_advanced_search_$$"
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
    echo "Usage: $0 <search_term> [OPTIONS]"
    echo "Options:"
    echo "  --type TYPE     Model type (LORA, Checkpoint, etc.) [default: LORA]"
    echo "  --creator CREATOR  Creator username for creator-based search"
    echo "  --output-format FORMAT  Output format: json or table [default: json]"
    echo ""
    echo "Example: $0 \"Better detailed pussy and anus\" --type LORA"
    exit 1
}

# Parse command line arguments
SEARCH_TERM=""
MODEL_TYPE="LORA"
CREATOR=""
OUTPUT_FORMAT="json"

while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            MODEL_TYPE="$2"
            shift 2
            ;;
        --creator)
            CREATOR="$2"
            shift 2
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
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

# Function to encode query parameter
encode_query() {
    local query="$1"
    # URL encode the query (basic version - could be enhanced)
    echo "$query" | sed 's/ /%20/g' | sed 's/&/%26/g' | sed 's/+/%2B/g' | sed 's/(/%28/g' | sed 's/)/%29/g'
}

ENCODED_QUERY=$(encode_query "$SEARCH_TERM")

# Function to calculate score for a search result
calculate_score() {
    local item_name="$1"
    local search_term="$2"
    local found_by="$3"
    
    local score=0
    
    # Case-insensitive matching
    local item_lower=$(echo "$item_name" | tr '[:upper:]' '[:lower:]')
    local search_lower=$(echo "$search_term" | tr '[:upper:]' '[:lower:]')
    
    # Exact name match: +100
    if [[ "$item_lower" == "$search_lower" ]]; then
        score=$((score + 100))
    fi
    
    # Partial name match: +50
    if [[ "$item_lower" =~ .*"$search_lower".* ]] || [[ "$search_lower" =~ .*"$item_lower".* ]]; then
        score=$((score + 50))
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
    
    # safetensors format bonus: +5 (if it's a model file)
    if [[ "$item_name" =~ \.safetensors$ ]]; then
        score=$((score + 5))
    fi
    
    # Direct ID lookup bonus: +50 (since it's 100% accurate)
    if [[ "$found_by" == "direct_id" ]]; then
        score=$((score + 50))
    fi
    
    echo "$score"
}

# Function to check known models file for direct match
check_known_models() {
    if [[ ! -f "$KNOWN_MODELS_FILE" ]]; then
        return 1
    fi
    
    # Check if search term matches any known model name
    local model_entry
    model_entry=$(jq -r --arg term "$SEARCH_TERM" '
        to_entries[] | 
        select(.key | test($term; "i")) | 
        .value' "$KNOWN_MODELS_FILE" 2>/dev/null || true)
    
    if [[ -n "$model_entry" ]] && [[ "$model_entry" != "null" ]]; then
        local model_id
        model_id=$(echo "$model_entry" | jq -r '.model_id')
        local model_name
        model_name=$(echo "$model_entry" | jq -r '.model_name')
        local model_type
        model_type=$(echo "$model_entry" | jq -r '.type')
        
        # Fetch model details via direct ID lookup
        local headers=()
        if [[ -n "$CIVITAI_API_KEY" ]]; then
            headers+=("-H" "Authorization: Bearer $CIVITAI_API_KEY")
        fi
        
        local response
        response=$(curl -s -w "\n%{http_code}" "${headers[@]}" "${API_BASE_URL}/models/${model_id}" || true)
        local http_code
        http_code=$(echo "$response" | tail -n1)
        local body
        body=$(echo "$response" | head -n -1)
        
        if [[ "$http_code" -eq 200 ]]; then
            # Find the file to download
            local filename
            filename=$(echo "$body" | jq -r '.modelVersions[0].files[0].name // "unknown.safetensors"')
            local version_id
            version_id=$(echo "$body" | jq -r '.modelVersions[0].id // "unknown"')
            local creator
            creator=$(echo "$body" | jq -r '.creator.username // "unknown"')
            
            local score
            score=$(calculate_score "$model_name" "$SEARCH_TERM" "direct_id")
            
            # Output in the required format
            if [[ "$OUTPUT_FORMAT" == "json" ]]; then
                echo "{"
                echo "  \"model_id\": $model_id,"
                echo "  \"name\": \"$model_name\","
                echo "  \"filename\": \"$filename\","
                echo "  \"version\": \"${body}\" | jq -r '.modelVersions[0].name // \"unknown\"',"
                echo "  \"version_id\": $version_id,"
                echo "  \"score\": $score,"
                echo "  \"confidence\": \"high\","
                echo "  \"found_by\": \"direct_id\","
                echo "  \"download_url\": \"https://civitai.com/api/download/models/$version_id\","
                echo "  \"creator\": \"$creator\""
                echo "}"
            else
                echo -e "${GREEN}✓${NC} Direct ID match found:"
                echo "  ID: $model_id"
                echo "  Name: $model_name"
                echo "  Filename: $filename"
                echo "  Score: $score"
                echo "  Confidence: high"
                echo "  Found by: direct_id"
            fi
            
            # Store result temporarily for later processing
            echo "$body" > "$TEMP_DIR/direct_result.json"
            echo "$score" > "$TEMP_DIR/direct_score.txt"
            return 0
        fi
    fi
    
    return 1
}

# Function to perform query search with various parameters
perform_query_search() {
    local query="$1"
    local nsfw="$2"
    local sort_order="${3:-Highest Rated}"
    
    local api_url="${API_BASE_URL}/models?query=${query}&types=${MODEL_TYPE}&limit=10&sort=${sort_order// /%20}"
    
    if [[ "$nsfw" == "true" ]]; then
        api_url="${api_url}&nsfw=true"
    fi
    
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

# Function to perform tag-based search
perform_tag_search() {
    local tag="$1"
    local api_url="${API_BASE_URL}/models?tag=${tag}&types=${MODEL_TYPE}&nsfw=true&limit=5"
    
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

# Function to perform creator-based search
perform_creator_search() {
    local username="$1"
    local api_url="${API_BASE_URL}/models?username=${username}&types=${MODEL_TYPE}&nsfw=true&limit=10"
    
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

# Function to extract tags from search term
extract_tags_from_query() {
    local query="$1"
    local tags=()
    
    # Common anatomical terms
    local anatomical_terms=("anatomy" "anatomical" "detail" "details" "eyes" "pussy" "anus" "breasts" "ass" "thighs")
    # Common style terms
    local style_terms=("realistic" "high" "definition" "hd" "detailed" "detail")
    # Common content terms
    local content_terms=("nsfw" "explicit" "nude" "naked" "adult")
    
    # Convert to lowercase for matching
    local query_lower=$(echo "$query" | tr '[:upper:]' '[:lower:]')
    
    # Extract known tags
    for term in "${anatomical_terms[@]}" "${style_terms[@]}" "${content_terms[@]}"; do
        if [[ "$query_lower" == *"$term"* ]]; then
            tags+=("$term")
        fi
    done
    
    # Extract individual words (longer than 2 chars, not common words)
    local words
    read -ra words <<< "$query"
    for word in "${words[@]}"; do
        local word_lower=$(echo "$word" | tr '[:upper:]' '[:lower:]')
        # Skip common words
        if [[ ! "$word_lower" =~ ^(and|the|for|with|v[0-9]*|xl|v[0-9]\.[0-9])$ ]] && [[ ${#word} -gt 2 ]]; then
            # Add if not already in tags
            local found=0
            for existing_tag in "${tags[@]}"; do
                if [[ "$existing_tag" == "$word_lower" ]]; then
                    found=1
                    break
                fi
            done
            if [[ $found -eq 0 ]]; then
                tags+=("$word_lower")
            fi
        fi
    done
    
    # Output tags
    for tag in "${tags[@]}"; do
        echo "$tag"
    done
}

log_info "Starting advanced Civitai search for: \"$SEARCH_TERM\" (Type: $MODEL_TYPE)"

# Initialize results array
results_file="$TEMP_DIR/results.jsonl"
> "$results_file"

# Strategy 1: Check known models first (this is the fastest approach)
log_info "Strategy 1: Checking known models mapping..."
if check_known_models; then
    log_success "Found in known models, returning immediately"
    
    # Clean up
    rm -rf "$TEMP_DIR"
    exit 0
else
    log_info "No direct match in known models, continuing with other strategies"
fi

# Strategy 2: Query searches (multiple parameter combinations)
log_info "Strategy 2: Trying query searches..."
strategies_tried=()

# Try with nsfw=true
log_info "  Query search with nsfw=true..."
query_result=$(perform_query_search "$ENCODED_QUERY" "true" || true)
if [[ -n "$query_result" ]]; then
    strategies_tried+=("query_nsfw")
    
    # Process query results
    local item_count
    item_count=$(echo "$query_result" | jq -r '.items | length' 2>/dev/null || echo "0")
    
    for i in $(seq 0 $((item_count > 10 ? 9 : item_count - 1)) 2>/dev/null); do
        if [[ $i -ge $item_count ]]; then
            break
        fi
        
        local item_id
        item_id=$(echo "$query_result" | jq -r ".items[$i].id" 2>/dev/null || echo "null")
        local item_name
        item_name=$(echo "$query_result" | jq -r ".items[$i].name" 2>/dev/null || echo "null")
        local item_type
        item_type=$(echo "$query_result" | jq -r ".items[$i].type" 2>/dev/null || echo "null")
        
        if [[ "$item_id" != "null" ]] && [[ "$item_name" != "null" ]]; then
            local score
            score=$(calculate_score "$item_name" "$SEARCH_TERM" "query")
            
            # Find the best file for download
            local filename
            filename=$(echo "$query_result" | jq -r ".items[$i].modelVersions[0].files[0].name // \"unknown.safetensors\"" 2>/dev/null)
            local version_id
            version_id=$(echo "$query_result" | jq -r ".items[$i].modelVersions[0].id // \"unknown\"" 2>/dev/null)
            
            # Output result in JSON format
            echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"score\": $score, \"confidence\": \"$(if [[ $score -ge 75 ]]; then echo "high"; elif [[ $score -ge 50 ]]; then echo "medium"; else echo "low"; fi)\", \"found_by\": \"query\", \"type\": \"$item_type\", \"filename\": \"$filename\", \"version_id\": $version_id }" >> "$results_file"
        fi
    done
fi

# Try without nsfw parameter
log_info "  Query search without nsfw parameter..."
query_result_no_nsfw=$(perform_query_search "$ENCODED_QUERY" "false" || true)
if [[ -n "$query_result_no_nsfw" ]]; then
    strategies_tried+=("query_without_nsfw")
    
    local item_count
    item_count=$(echo "$query_result_no_nsfw" | jq -r '.items | length' 2>/dev/null || echo "0")
    
    for i in $(seq 0 $((item_count > 5 ? 4 : item_count - 1)) 2>/dev/null); do
        if [[ $i -ge $item_count ]]; then
            break
        fi
        
        local item_id
        item_id=$(echo "$query_result_no_nsfw" | jq -r ".items[$i].id" 2>/dev/null || echo "null")
        local item_name
        item_name=$(echo "$query_result_no_nsfw" | jq -r ".items[$i].name" 2>/dev/null || echo "null")
        local item_type
        item_type=$(echo "$query_result_no_nsfw" | jq -r ".items[$i].type" 2>/dev/null || echo "null")
        
        if [[ "$item_id" != "null" ]] && [[ "$item_name" != "null" ]]; then
            local score
            score=$(calculate_score "$item_name" "$SEARCH_TERM" "query")
            
            # Find the best file for download
            local filename
            filename=$(echo "$query_result_no_nsfw" | jq -r ".items[$i].modelVersions[0].files[0].name // \"unknown.safetensors\"" 2>/dev/null)
            local version_id
            version_id=$(echo "$query_result_no_nsfw" | jq -r ".items[$i].modelVersions[0].id // \"unknown\"" 2>/dev/null)
            
            # Output result in JSON format
            echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"score\": $score, \"confidence\": \"$(if [[ $score -ge 75 ]]; then echo "high"; elif [[ $score -ge 50 ]]; then echo "medium"; else echo "low"; fi)\", \"found_by\": \"query\", \"type\": \"$item_type\", \"filename\": \"$filename\", \"version_id\": $version_id }" >> "$results_file"
        fi
    done
fi

# Try with different sort order
log_info "  Query search with sort=Most Downloaded..."
query_result_downloads=$(perform_query_search "$ENCODED_QUERY" "true" "Most Downloaded" || true)
if [[ -n "$query_result_downloads" ]]; then
    strategies_tried+=("query_most_downloaded")
    
    local item_count
    item_count=$(echo "$query_result_downloads" | jq -r '.items | length' 2>/dev/null || echo "0")
    
    for i in $(seq 0 $((item_count > 3 ? 2 : item_count - 1)) 2>/dev/null); do
        if [[ $i -ge $item_count ]]; then
            break
        fi
        
        local item_id
        item_id=$(echo "$query_result_downloads" | jq -r ".items[$i].id" 2>/dev/null || echo "null")
        local item_name
        item_name=$(echo "$query_result_downloads" | jq -r ".items[$i].name" 2>/dev/null || echo "null")
        local item_type
        item_type=$(echo "$query_result_downloads" | jq -r ".items[$i].type" 2>/dev/null || echo "null")
        
        if [[ "$item_id" != "null" ]] && [[ "$item_name" != "null" ]]; then
            local score
            score=$(calculate_score "$item_name" "$SEARCH_TERM" "query")
            
            # Find the best file for download
            local filename
            filename=$(echo "$query_result_downloads" | jq -r ".items[$i].modelVersions[0].files[0].name // \"unknown.safetensors\"" 2>/dev/null)
            local version_id
            version_id=$(echo "$query_result_downloads" | jq -r ".items[$i].modelVersions[0].id // \"unknown\"" 2>/dev/null)
            
            # Output result in JSON format
            echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"score\": $score, \"confidence\": \"$(if [[ $score -ge 75 ]]; then echo "high"; elif [[ $score -ge 50 ]]; then echo "medium"; else echo "low"; fi)\", \"found_by\": \"query\", \"type\": \"$item_type\", \"filename\": \"$filename\", \"version_id\": $version_id }" >> "$results_file"
        fi
    done
fi

# Strategy 3: Tag-based search
log_info "Strategy 3: Trying tag-based search..."
all_tags=()
while IFS= read -r tag; do
    all_tags+=("$tag")
done < <(extract_tags_from_query "$SEARCH_TERM")

for tag in "${all_tags[@]}"; do
    log_info "  Trying tag: $tag"
    tag_result=$(perform_tag_search "$tag" || true)
    if [[ -n "$tag_result" ]]; then
        strategies_tried+=("tag_$tag")
        
        local item_count
        item_count=$(echo "$tag_result" | jq -r '.items | length' 2>/dev/null || echo "0")
        
        for i in $(seq 0 $((item_count > 5 ? 4 : item_count - 1)) 2>/dev/null); do
            if [[ $i -ge $item_count ]]; then
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
                score=$(calculate_score "$item_name" "$SEARCH_TERM" "tag")
                
                # Find the best file for download
                local filename
                filename=$(echo "$tag_result" | jq -r ".items[$i].modelVersions[0].files[0].name // \"unknown.safetensors\"" 2>/dev/null)
                local version_id
                version_id=$(echo "$tag_result" | jq -r ".items[$i].modelVersions[0].id // \"unknown\"" 2>/dev/null)
                
                # Output result in JSON format
                echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"score\": $score, \"confidence\": \"$(if [[ $score -ge 75 ]]; then echo "high"; elif [[ $score -ge 50 ]]; then echo "medium"; else echo "low"; fi)\", \"found_by\": \"tag\", \"tag_used\": \"$tag\", \"type\": \"$item_type\", \"filename\": \"$filename\", \"version_id\": $version_id }" >> "$results_file"
            fi
        done
    fi
done

# Strategy 4: Creator-based search (if creator provided)
if [[ -n "$CREATOR" ]]; then
    log_info "Strategy 4: Trying creator-based search for: $CREATOR"
    creator_result=$(perform_creator_search "$CREATOR" || true)
    if [[ -n "$creator_result" ]]; then
        strategies_tried+=("creator")
        
        local item_count
        item_count=$(echo "$creator_result" | jq -r '.items | length' 2>/dev/null || echo "0")
        
        for i in $(seq 0 $((item_count > 10 ? 9 : item_count - 1)) 2>/dev/null); do
            if [[ $i -ge $item_count ]]; then
                break
            fi
            
            local item_id
            item_id=$(echo "$creator_result" | jq -r ".items[$i].id" 2>/dev/null || echo "null")
            local item_name
            item_name=$(echo "$creator_result" | jq -r ".items[$i].name" 2>/dev/null || echo "null")
            local item_type
            item_type=$(echo "$creator_result" | jq -r ".items[$i].type" 2>/dev/null || echo "null")
            
            if [[ "$item_id" != "null" ]] && [[ "$item_name" != "null" ]]; then
                local score
                score=$(calculate_score "$item_name" "$SEARCH_TERM" "creator")
                
                # Find the best file for download
                local filename
                filename=$(echo "$creator_result" | jq -r ".items[$i].modelVersions[0].files[0].name // \"unknown.safetensors\"" 2>/dev/null)
                local version_id
                version_id=$(echo "$creator_result" | jq -r ".items[$i].modelVersions[0].id // \"unknown\"" 2>/dev/null)
                
                # Output result in JSON format
                echo "{ \"model_id\": $item_id, \"name\": \"$item_name\", \"score\": $score, \"confidence\": \"$(if [[ $score -ge 75 ]]; then echo "high"; elif [[ $score -ge 50 ]]; then echo "medium"; else echo "low"; fi)\", \"found_by\": \"creator\", \"creator\": \"$CREATOR\", \"type\": \"$item_type\", \"filename\": \"$filename\", \"version_id\": $version_id }" >> "$results_file"
            fi
        done
    fi
fi

# Compile and sort results
if [[ -s "$results_file" ]]; then
    log_info "Processing results..."
    
    # Read all results, sort by score descending, and format output
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{"
        echo "  \"query\": \"$SEARCH_TERM\","
        echo "  \"model_type\": \"$MODEL_TYPE\","
        echo "  \"strategies_tried\": [$(printf '%s,' "${strategies_tried[@]}" | sed 's/,$//')],"
        echo "  \"candidates\": ["
        
        # Sort results by score (highest first)
        local first_result=1
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                if [[ $first_result -eq 0 ]]; then
                    echo ","
                else
                    first_result=0
                fi
                echo "    $line" | sed 's/^  //'
            fi
        done < <(sort -t',' -k2 -nr "$results_file")  # Sort by score field
        
        echo
        echo "  ]"
        echo "}"
    else
        echo "Query: $SEARCH_TERM"
        echo "Model Type: $MODEL_TYPE"
        echo "Strategies tried: ${strategies_tried[*]}"
        echo
        echo "Top Candidates:"
        
        local count=1
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                local model_id
                model_id=$(echo "$line" | jq -r '.model_id // "N/A"')
                local name
                name=$(echo "$line" | jq -r '.name // "N/A"')
                local score
                score=$(echo "$line" | jq -r '.score // "N/A"')
                local confidence
                confidence=$(echo "$line" | jq -r '.confidence // "N/A"')
                local found_by
                found_by=$(echo "$line" | jq -r '.found_by // "N/A"')
                
                echo "[$count] ID: $model_id | Name: \"$name\" | Score: $score | Confidence: $confidence | Found by: $found_by"
                ((count++))
                if [[ $count -gt 5 ]]; then  # Show top 5
                    break
                fi
            fi
        done < <(sort -t',' -k2 -nr "$results_file")  # Sort by score field
    fi
else
    log_warning "No results found with any strategy"
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "{"
        echo "  \"query\": \"$SEARCH_TERM\","
        echo "  \"model_type\": \"$MODEL_TYPE\","
        echo "  \"strategies_tried\": [$(printf '%s,' "${strategies_tried[@]}" | sed 's/,$//')],"
        echo "  \"candidates\": []"
        echo "}"
    else
        echo "Query: $SEARCH_TERM"
        echo "Model Type: $MODEL_TYPE"
        echo "No candidates found with any strategy."
        echo "Try alternative search terms or check if the model exists on Civitai directly."
    fi
fi

# Clean up
rm -rf "$TEMP_DIR"