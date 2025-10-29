"""
Civitai Search Diagnostics - Python Implementation

Ported from bash/debug_civitai_search.sh
Shows exact API queries, raw responses, scoring breakdowns,
and suggests alternative approaches when search fails.
"""

import json
import os
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class DiagnosticLevel(str, Enum):
    """Diagnostic message levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DiagnosticMessage:
    """A diagnostic message"""
    level: DiagnosticLevel
    category: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class SearchDiagnostic:
    """Complete diagnostic report for a search"""
    search_term: str
    model_type: str
    nsfw: bool

    # Results
    query_results: Optional[Dict[str, Any]] = None
    query_no_nsfw_results: Optional[Dict[str, Any]] = None
    tag_results: Dict[str, List[Dict]] = None

    # API details
    api_url: Optional[str] = None
    http_status: Optional[int] = None

    # Diagnostics
    messages: List[DiagnosticMessage] = None
    suggestions: List[str] = None

    def __post_init__(self):
        if self.tag_results is None:
            self.tag_results = {}
        if self.messages is None:
            self.messages = []
        if self.suggestions is None:
            self.suggestions = []

    def add_message(self, level: DiagnosticLevel, category: str,
                   message: str, details: Optional[Dict] = None):
        """Add a diagnostic message"""
        self.messages.append(DiagnosticMessage(level, category, message, details))

    def add_suggestion(self, suggestion: str):
        """Add a suggestion"""
        self.suggestions.append(suggestion)


class CivitaiSearchDebugger:
    """
    Diagnostic tool for Civitai search issues.

    Ported from bash/debug_civitai_search.sh
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('CIVITAI_API_KEY', '')
        self.base_url = "https://civitai.com/api/v1"

    def diagnose_search(self, search_term: str, model_type: str = "LORA",
                       nsfw: bool = True) -> SearchDiagnostic:
        """
        Run comprehensive search diagnostics.

        Port of main diagnostic flow from bash (lines 113-300).

        Args:
            search_term: Term to search for
            model_type: Model type filter
            nsfw: Include NSFW results

        Returns:
            SearchDiagnostic with complete analysis
        """
        diagnostic = SearchDiagnostic(
            search_term=search_term,
            model_type=model_type,
            nsfw=nsfw
        )

        diagnostic.add_message(
            DiagnosticLevel.INFO,
            "search",
            f"Starting diagnostic for: '{search_term}'"
        )

        # Strategy 1: Query search with nsfw parameter
        print("\n=== Query Search (nsfw={}) ===".format(nsfw))
        query_result = self._test_query_search(search_term, model_type, nsfw)
        diagnostic.query_results = query_result

        if query_result.get('status') == 'success':
            items = query_result.get('items', [])
            diagnostic.add_message(
                DiagnosticLevel.SUCCESS if items else DiagnosticLevel.WARNING,
                "query_search",
                f"Query search returned {len(items)} results",
                {'item_count': len(items)}
            )
            self._print_candidates(items[:5], "Query Search Results")
        else:
            diagnostic.add_message(
                DiagnosticLevel.ERROR,
                "query_search",
                f"Query search failed: {query_result.get('error')}",
                {'http_status': query_result.get('http_status')}
            )

        # Strategy 2: Try without NSFW flag if initial search had issues
        if not diagnostic.query_results.get('items') or \
           diagnostic.query_results.get('status') != 'success':
            print("\n=== Query Search (without NSFW flag) ===")
            query_no_nsfw = self._test_query_search(search_term, model_type, False)
            diagnostic.query_no_nsfw_results = query_no_nsfw

            if query_no_nsfw.get('status') == 'success':
                items = query_no_nsfw.get('items', [])
                diagnostic.add_message(
                    DiagnosticLevel.INFO,
                    "query_no_nsfw",
                    f"Query without NSFW returned {len(items)} results",
                    {'item_count': len(items)}
                )

        # Strategy 3: Tag-based search
        print("\n=== Tag-based Search ===")
        tags = self._extract_tags(search_term)
        diagnostic.add_message(
            DiagnosticLevel.INFO,
            "tag_extraction",
            f"Extracted tags: {', '.join(tags)}"
        )

        for tag in tags[:3]:  # Test first 3 tags
            print(f"\nTrying tag: {tag}")
            tag_result = self._test_tag_search(tag, model_type)

            if tag_result.get('status') == 'success':
                items = tag_result.get('items', [])
                diagnostic.tag_results[tag] = items
                diagnostic.add_message(
                    DiagnosticLevel.SUCCESS if items else DiagnosticLevel.WARNING,
                    "tag_search",
                    f"Tag '{tag}' returned {len(items)} results",
                    {'tag': tag, 'item_count': len(items)}
                )

                if items:
                    first_item = items[0]
                    print(f"  First result: {first_item.get('name')} (ID: {first_item.get('id')})")

        # Generate diagnosis and suggestions
        self._generate_diagnosis(diagnostic)
        self._generate_suggestions(diagnostic)

        return diagnostic

    def _test_query_search(self, query: str, model_type: str,
                          nsfw: bool) -> Dict[str, Any]:
        """Test query search and return detailed results"""
        params = {
            'query': query,
            'types': model_type,
            'limit': 10,
            'sort': 'Highest Rated'
        }

        if nsfw:
            params['nsfw'] = 'true'

        api_url = f"{self.base_url}/models"
        print(f"API URL: {api_url}")
        print(f"Parameters: {params}")

        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            http_status = response.status_code

            print(f"Response: HTTP {http_status}")

            if http_status == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"Items returned: {len(items)}")

                return {
                    'status': 'success',
                    'http_status': http_status,
                    'items': items,
                    'api_url': api_url,
                    'params': params
                }
            else:
                return {
                    'status': 'error',
                    'http_status': http_status,
                    'error': f'HTTP {http_status}',
                    'api_url': api_url,
                    'params': params
                }

        except Exception as e:
            print(f"Error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'api_url': api_url,
                'params': params
            }

    def _test_tag_search(self, tag: str, model_type: str) -> Dict[str, Any]:
        """Test tag-based search"""
        params = {
            'tag': tag,
            'types': model_type,
            'nsfw': 'true',
            'limit': 5
        }

        api_url = f"{self.base_url}/models"

        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            http_status = response.status_code

            print(f"  Response: HTTP {http_status}")

            if http_status == 200:
                data = response.json()
                items = data.get('items', [])
                print(f"  Items returned: {len(items)}")

                return {
                    'status': 'success',
                    'http_status': http_status,
                    'items': items
                }
            else:
                return {
                    'status': 'error',
                    'http_status': http_status,
                    'error': f'HTTP {http_status}'
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _extract_tags(self, query: str) -> List[str]:
        """Extract potential tags from query"""
        # Port of tag extraction from bash (lines 169-214)
        anatomical_terms = ['anatomy', 'anatomical', 'detail', 'details',
                           'eyes', 'pussy', 'anus', 'breasts', 'ass', 'thighs']
        style_terms = ['realistic', 'high', 'definition', 'hd', 'detailed', 'detail']
        content_terms = ['nsfw', 'explicit', 'nude', 'naked', 'adult']

        all_terms = anatomical_terms + style_terms + content_terms
        found_tags = []

        query_lower = query.lower()

        # Extract known terms
        for term in all_terms:
            if term in query_lower:
                found_tags.append(term)

        # Extract individual words
        words = query.split()
        skip_words = {'and', 'the', 'for', 'with', 'v1', 'v2', 'v3', 'xl'}

        for word in words:
            word_clean = word.strip().lower()
            if len(word_clean) > 2 and word_clean not in skip_words:
                if word_clean not in found_tags:
                    found_tags.append(word_clean)

        return found_tags

    def _print_candidates(self, items: List[Dict], title: str):
        """Print candidate results in readable format"""
        if not items:
            print(f"{title}: No results")
            return

        print(f"\n{title}:")
        for i, item in enumerate(items, 1):
            model_id = item.get('id', 'N/A')
            name = item.get('name', 'N/A')
            model_type = item.get('type', 'N/A')
            print(f"  [{i}] ID: {model_id} | Name: \"{name}\" | Type: {model_type}")

    def _generate_diagnosis(self, diagnostic: SearchDiagnostic):
        """
        Generate diagnosis from results.

        Port of DIAGNOSIS section from bash (lines 256-286).
        """
        print("\n=== DIAGNOSIS ===")

        query_results = diagnostic.query_results or {}

        if query_results.get('status') == 'success':
            items = query_results.get('items', [])

            if len(items) == 0:
                diagnostic.add_message(
                    DiagnosticLevel.WARNING,
                    "diagnosis",
                    "Query search returned 0 results - likely term filtering"
                )
                print("⚠️  [DIAGNOSIS] Query search returned 0 results - likely term filtering")

            elif len(items) > 0:
                # Check if results match search term
                found_match = False
                search_term_lower = diagnostic.search_term.lower()

                for item in items:
                    item_name = item.get('name', '')
                    if search_term_lower in item_name.lower():
                        found_match = True
                        break

                if not found_match:
                    diagnostic.add_message(
                        DiagnosticLevel.WARNING,
                        "diagnosis",
                        "Query search found results but none match search terms exactly"
                    )
                    print("⚠️  [DIAGNOSIS] Query search found results but none match search terms exactly")
                else:
                    diagnostic.add_message(
                        DiagnosticLevel.SUCCESS,
                        "diagnosis",
                        "Found potentially matching results"
                    )
                    print("✓ [DIAGNOSIS] Found potentially matching results")
        else:
            diagnostic.add_message(
                DiagnosticLevel.ERROR,
                "diagnosis",
                "API request failed - check your connection and API key"
            )
            print("✗ [DIAGNOSIS] API request failed - check your connection and API key")

    def _generate_suggestions(self, diagnostic: SearchDiagnostic):
        """
        Generate suggestions based on diagnostic results.

        Port of SUGGESTIONS section from bash (lines 289-300).
        """
        print("\n=== SUGGESTIONS ===")

        query_results = diagnostic.query_results or {}

        if query_results.get('status') != 'success' or \
           len(query_results.get('items', [])) == 0:

            diagnostic.add_suggestion("Try direct ID lookup if model URL is known")
            print("💡 [SUGGESTION] Try direct ID lookup if model URL is known")

            if diagnostic.tag_results:
                tags_found = [tag for tag, items in diagnostic.tag_results.items() if items]
                if tags_found:
                    diagnostic.add_suggestion(f"Try tag search with: {', '.join(tags_found)}")
                    print(f"💡 [SUGGESTION] Try tag search with: {', '.join(tags_found)}")
            else:
                diagnostic.add_suggestion("Try tag search: anatomy, detail, nsfw")
                print("💡 [SUGGESTION] Try tag search: anatomy, detail, nsfw")

        diagnostic.add_suggestion("Check for alternative names or creators")
        print("💡 [SUGGESTION] Check for alternative names or creators")

        diagnostic.add_suggestion("Try the advanced multi-strategy search")
        print("💡 [SUGGESTION] Try the advanced multi-strategy search")

    def export_report(self, diagnostic: SearchDiagnostic,
                     output_file: Optional[str] = None) -> str:
        """Export diagnostic report as JSON"""
        report = {
            'search_term': diagnostic.search_term,
            'model_type': diagnostic.model_type,
            'nsfw': diagnostic.nsfw,
            'query_results': diagnostic.query_results,
            'query_no_nsfw_results': diagnostic.query_no_nsfw_results,
            'tag_results': diagnostic.tag_results,
            'messages': [
                {
                    'level': msg.level.value,
                    'category': msg.category,
                    'message': msg.message,
                    'details': msg.details
                }
                for msg in diagnostic.messages
            ],
            'suggestions': diagnostic.suggestions
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            return output_file

        return json.dumps(report, indent=2)


def main():
    """CLI interface for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Civitai search debugger - diagnose search failures'
    )
    parser.add_argument('search_term', help='Model name or description to search for')
    parser.add_argument('--type', default='LORA', help='Model type (default: LORA)')
    parser.add_argument('--nsfw', type=bool, default=True,
                       help='Include NSFW results (default: true)')
    parser.add_argument('--export', help='Export diagnostic report to JSON file')

    args = parser.parse_args()

    debugger = CivitaiSearchDebugger()
    diagnostic = debugger.diagnose_search(args.search_term, args.type, args.nsfw)

    if args.export:
        debugger.export_report(diagnostic, args.export)
        print(f"\n📄 Diagnostic report exported to: {args.export}")


if __name__ == '__main__':
    main()
