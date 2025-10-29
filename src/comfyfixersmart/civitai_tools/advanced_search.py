"""
Advanced Civitai Search - Python Implementation

Ported from bash/advanced_civitai_search.sh
Implements sophisticated search with cascading fallbacks:
1. Known models lookup (from known_models.json)
2. Query search (multiple parameter combinations)
3. Tag-based search (anatomical/detail/NSFW tags)
4. Creator-based search (if username known)

Scoring system prioritizes exact matches while allowing partial matches for discovery.
"""

import json
import os
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class ConfidenceLevel(str, Enum):
    """Match confidence levels"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SearchStrategy(str, Enum):
    """Search strategy types"""

    DIRECT_ID = "direct_id"
    QUERY = "query"
    QUERY_NSFW = "query_nsfw"
    QUERY_NO_NSFW = "query_no_nsfw"
    TAG = "tag"
    CREATOR = "creator"


@dataclass
class SearchCandidate:
    """A candidate model from search results"""

    model_id: int
    name: str
    filename: str
    version_id: int
    version_name: str
    score: int
    confidence: ConfidenceLevel
    found_by: SearchStrategy
    type: str
    download_url: str
    creator: Optional[str] = None
    tag_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        return asdict(self)


class ModelScorer:
    """Calculates relevance scores for search results"""

    @staticmethod
    def calculate_score(item_name: str, search_term: str, found_by: SearchStrategy) -> int:
        """
        Calculate relevance score for a search result.

        Port of calculate_score() from bash script (lines 91-133).

        Args:
            item_name: Name of the model from API
            search_term: Original search query
            found_by: Strategy that found this result

        Returns:
            Integer score (higher is better)
        """
        score = 0

        # Normalize for case-insensitive comparison
        item_lower = item_name.lower()
        search_lower = search_term.lower()

        # Exact name match: +100
        if item_lower == search_lower:
            score += 100

        # Partial name match: +50
        if search_lower in item_lower or item_lower in search_lower:
            score += 50

        # Keyword matches: +25 per keyword
        keywords = search_term.split()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if len(keyword_lower) > 2 and keyword_lower in item_lower:
                score += 25

        # Safetensors format bonus: +5
        if item_name.endswith(".safetensors"):
            score += 5

        # Direct ID lookup bonus: +50 (100% accurate)
        if found_by == SearchStrategy.DIRECT_ID:
            score += 50

        return score

    @staticmethod
    def get_confidence_level(score: int) -> ConfidenceLevel:
        """Convert score to confidence level"""
        if score >= 75:
            return ConfidenceLevel.HIGH
        elif score >= 50:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


class TagExtractor:
    """Extracts search tags from query strings"""

    # Port of anatomical/style/content terms from bash (lines 303-308)
    ANATOMICAL_TERMS = [
        "anatomy",
        "anatomical",
        "detail",
        "details",
        "eyes",
        "pussy",
        "anus",
        "breasts",
        "ass",
        "thighs",
    ]

    STYLE_TERMS = ["realistic", "high", "definition", "hd", "detailed", "detail"]

    CONTENT_TERMS = ["nsfw", "explicit", "nude", "naked", "adult"]

    # Words to skip (lines 325)
    SKIP_WORDS = {"and", "the", "for", "with", "v1", "v2", "v3", "xl"}

    @classmethod
    def extract_tags(cls, query: str) -> List[str]:
        """
        Extract potential tags from search query.

        Port of extract_tags_from_query() from bash (lines 456-478).

        Args:
            query: Search query string

        Returns:
            List of potential tag strings
        """
        tags = []
        query_lower = query.lower()

        # Extract known terms
        all_terms = cls.ANATOMICAL_TERMS + cls.STYLE_TERMS + cls.CONTENT_TERMS
        for term in all_terms:
            if term in query_lower:
                tags.append(term)

        # Extract individual words (longer than 2 chars, not common words)
        words = query.split()
        for word in words:
            word_clean = re.sub(r"[^a-zA-Z0-9]", "", word)
            word_lower = word_clean.lower()

            if len(word_lower) > 2 and word_lower not in cls.SKIP_WORDS:
                if word_lower not in tags:
                    tags.append(word_lower)

        return tags


class KnownModelsDB:
    """Manages known model ID mappings"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "known_models.json"

        self.config_path = Path(config_path)
        self.models = self._load_models()

    def _load_models(self) -> Dict[str, Any]:
        """Load known models from JSON file"""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load known models: {e}")
            return {}

    def lookup(self, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Check if search term matches a known model.

        Port of check_known_models() from bash (lines 136-213).

        Args:
            search_term: Search query

        Returns:
            Model info dict if found, None otherwise
        """
        search_lower = search_term.lower()

        for known_name, model_info in self.models.items():
            if search_lower in known_name.lower():
                return model_info

        return None


class AdvancedCivitaiSearch:
    """
    Advanced multi-strategy Civitai search implementation.

    Ported from bash/advanced_civitai_search.sh
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CIVITAI_API_KEY", "")
        self.base_url = "https://civitai.com/api/v1"
        self.scorer = ModelScorer()
        self.tag_extractor = TagExtractor()
        self.known_models = KnownModelsDB()

    def search(
        self, search_term: str, model_type: str = "LORA", creator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute advanced multi-strategy search.

        Port of main search logic from bash (lines 346-636).

        Args:
            search_term: Model name or description to search for
            model_type: Type filter (LORA, Checkpoint, etc.)
            creator: Optional creator username

        Returns:
            Dict with query, strategies tried, and candidates
        """
        results = {
            "query": search_term,
            "model_type": model_type,
            "strategies_tried": [],
            "candidates": [],
        }

        # Strategy 1: Check known models first (fastest)
        known_result = self._check_known_models(search_term, model_type)
        if known_result:
            results["strategies_tried"].append(SearchStrategy.DIRECT_ID.value)
            results["candidates"].append(known_result.to_dict())
            return results

        # Strategy 2: Query search with nsfw=true
        query_results = self._search_query(search_term, model_type, nsfw=True)
        if query_results:
            results["strategies_tried"].append(SearchStrategy.QUERY_NSFW.value)
            results["candidates"].extend([r.to_dict() for r in query_results])

        # Strategy 3: Query search without nsfw parameter
        if len(results["candidates"]) < 5:
            query_no_nsfw = self._search_query(search_term, model_type, nsfw=False)
            if query_no_nsfw:
                results["strategies_tried"].append(SearchStrategy.QUERY_NO_NSFW.value)
                results["candidates"].extend([r.to_dict() for r in query_no_nsfw])

        # Strategy 4: Tag-based search
        if len(results["candidates"]) < 10:
            tag_results = self._search_by_tags(search_term, model_type)
            if tag_results:
                results["strategies_tried"].append(SearchStrategy.TAG.value)
                results["candidates"].extend([r.to_dict() for r in tag_results])

        # Strategy 5: Creator-based search (if provided)
        if creator and len(results["candidates"]) < 15:
            creator_results = self._search_by_creator(creator, model_type, search_term)
            if creator_results:
                results["strategies_tried"].append(SearchStrategy.CREATOR.value)
                results["candidates"].extend([r.to_dict() for r in creator_results])

        # Sort by score (highest first) and deduplicate
        results["candidates"] = self._deduplicate_and_sort(results["candidates"])

        return results

    def _check_known_models(self, search_term: str, model_type: str) -> Optional[SearchCandidate]:
        """
        Check known models database for direct match.

        Port of check_known_models() from bash (lines 136-213).
        """
        model_info = self.known_models.lookup(search_term)
        if not model_info:
            return None

        model_id = model_info.get("model_id")
        if not model_id:
            return None

        # Fetch model details via direct ID
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models/{model_id}", headers=headers, timeout=30
            )

            if response.status_code != 200:
                return None

            data = response.json()

            # Get latest version
            versions = data.get("modelVersions", [])
            if not versions:
                return None

            version = versions[0]
            version_id = version.get("id")

            # Get primary file
            files = version.get("files", [])
            primary_file = next((f for f in files if f.get("primary")), files[0] if files else None)

            if not primary_file:
                return None

            filename = primary_file.get("name", f"model_{model_id}.safetensors")
            model_name = data.get("name", f"Model {model_id}")

            score = self.scorer.calculate_score(model_name, search_term, SearchStrategy.DIRECT_ID)

            return SearchCandidate(
                model_id=model_id,
                name=model_name,
                filename=filename,
                version_id=version_id,
                version_name=version.get("name", f"Version {version_id}"),
                score=score,
                confidence=ConfidenceLevel.HIGH,
                found_by=SearchStrategy.DIRECT_ID,
                type=model_type,
                download_url=f"https://civitai.com/api/download/models/{version_id}",
                creator=data.get("creator", {}).get("username"),
                metadata={"direct_id_lookup": True},
            )

        except Exception as e:
            print(f"Error in direct ID lookup: {e}")
            return None

    def _search_query(self, query: str, model_type: str, nsfw: bool) -> List[SearchCandidate]:
        """
        Perform query search with optional NSFW parameter.

        Port of perform_query_search() from bash (lines 216-245).
        """
        try:
            params = {"query": query, "types": model_type, "limit": 10, "sort": "Highest Rated"}

            if nsfw:
                params["nsfw"] = "true"

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models", params=params, headers=headers, timeout=30
            )

            if response.status_code != 200:
                return []

            data = response.json()
            return self._process_search_results(
                data.get("items", []),
                query,
                SearchStrategy.QUERY_NSFW if nsfw else SearchStrategy.QUERY_NO_NSFW,
            )

        except Exception as e:
            print(f"Query search error: {e}")
            return []

    def _search_by_tags(self, query: str, model_type: str) -> List[SearchCandidate]:
        """
        Perform tag-based search.

        Port of tag-based search from bash (lines 480-523).
        """
        tags = self.tag_extractor.extract_tags(query)
        results = []

        for tag in tags[:5]:  # Limit to first 5 tags
            try:
                params = {"tag": tag, "types": model_type, "nsfw": "true", "limit": 5}

                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                response = requests.get(
                    f"{self.base_url}/models", params=params, headers=headers, timeout=30
                )

                if response.status_code != 200:
                    continue

                data = response.json()
                tag_results = self._process_search_results(
                    data.get("items", []), query, SearchStrategy.TAG
                )

                # Add tag metadata
                for result in tag_results:
                    result.tag_used = tag

                results.extend(tag_results)

            except Exception as e:
                print(f"Tag search error for '{tag}': {e}")
                continue

        return results

    def _search_by_creator(
        self, creator: str, model_type: str, query: str
    ) -> List[SearchCandidate]:
        """
        Perform creator-based search.

        Port of creator search from bash (lines 525-562).
        """
        try:
            params = {"username": creator, "types": model_type, "nsfw": "true", "limit": 10}

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.get(
                f"{self.base_url}/models", params=params, headers=headers, timeout=30
            )

            if response.status_code != 200:
                return []

            data = response.json()
            return self._process_search_results(
                data.get("items", []), query, SearchStrategy.CREATOR
            )

        except Exception as e:
            print(f"Creator search error: {e}")
            return []

    def _process_search_results(
        self, items: List[Dict], query: str, strategy: SearchStrategy
    ) -> List[SearchCandidate]:
        """Process API search results into SearchCandidate objects"""
        candidates = []

        for item in items:
            model_id = item.get("id")
            model_name = item.get("name", "")

            # Get latest version
            versions = item.get("modelVersions", [])
            if not versions:
                continue

            version = versions[0]
            version_id = version.get("id")

            # Get primary file
            files = version.get("files", [])
            primary_file = next((f for f in files if f.get("primary")), files[0] if files else None)

            if not primary_file:
                continue

            filename = primary_file.get("name", f"model_{model_id}.safetensors")

            # Calculate score
            score = self.scorer.calculate_score(model_name, query, strategy)
            confidence = self.scorer.get_confidence_level(score)

            candidate = SearchCandidate(
                model_id=model_id,
                name=model_name,
                filename=filename,
                version_id=version_id,
                version_name=version.get("name", f"Version {version_id}"),
                score=score,
                confidence=confidence,
                found_by=strategy,
                type=item.get("type", "Unknown"),
                download_url=f"https://civitai.com/api/download/models/{version_id}",
                creator=item.get("creator", {}).get("username"),
            )

            candidates.append(candidate)

        return candidates

    def _deduplicate_and_sort(self, candidates: List[Dict]) -> List[Dict]:
        """Remove duplicates and sort by score"""
        seen = set()
        unique = []

        for candidate in candidates:
            model_id = candidate["model_id"]
            if model_id not in seen:
                seen.add(model_id)
                unique.append(candidate)

        return sorted(unique, key=lambda x: x["score"], reverse=True)


def main():
    """CLI interface for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Advanced Civitai Search with multi-strategy fallbacks"
    )
    parser.add_argument("search_term", help="Model name or description")
    parser.add_argument("--type", default="LORA", help="Model type (default: LORA)")
    parser.add_argument("--creator", help="Creator username for creator-based search")
    parser.add_argument(
        "--output-format",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    searcher = AdvancedCivitaiSearch()
    results = searcher.search(args.search_term, args.type, args.creator)

    if args.output_format == "json":
        print(json.dumps(results, indent=2))
    else:
        print(f"Query: {results['query']}")
        print(f"Model Type: {results['model_type']}")
        print(f"Strategies tried: {', '.join(results['strategies_tried'])}")
        print("\nTop Candidates:")
        for i, candidate in enumerate(results["candidates"][:10], 1):
            print(
                f"[{i}] Score: {candidate['score']} | "
                f"Name: {candidate['name']} | "
                f"ID: {candidate['model_id']} | "
                f"Confidence: {candidate['confidence']}"
            )


if __name__ == "__main__":
    main()
