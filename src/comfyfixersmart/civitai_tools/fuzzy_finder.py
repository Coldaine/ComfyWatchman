"""
Civitai Fuzzy Model Finder - Python Implementation

Ported from bash/fuzzy_civitai_finder.sh
Interactive tool to search and select models with fuzzy matching.
"""

import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from .advanced_search import AdvancedCivitaiSearch, SearchCandidate
from .direct_downloader import CivitaiDirectDownloader


@dataclass
class SelectionResult:
    """Result of user selection"""

    selected: bool
    candidate: Optional[SearchCandidate] = None
    action: Optional[str] = None  # 'download', 'info', 'cancel'


class CivitaiFuzzyFinder:
    """
    Interactive fuzzy model finder.

    Ported from bash/fuzzy_civitai_finder.sh
    Combines search with interactive selection.
    """

    def __init__(self):
        self.searcher = AdvancedCivitaiSearch()
        self.downloader = CivitaiDirectDownloader()

    def find_and_select(
        self, search_term: str, model_type: str = "LORA", auto_download: bool = False
    ) -> SelectionResult:
        """
        Search for models and let user select one.

        Args:
            search_term: Search query
            model_type: Model type filter
            auto_download: Automatically download top result

        Returns:
            SelectionResult with user choice
        """
        print(f"🔍 Searching for: {search_term}")
        print("=" * 60)

        # Perform search
        results = self.searcher.search(search_term, model_type)
        candidates = results.get("candidates", [])

        if not candidates:
            print("❌ No results found")
            print("\nSuggestions:")
            print("  - Try different search terms")
            print("  - Check spelling")
            print("  - Try broader search")
            return SelectionResult(selected=False)

        print(f"✅ Found {len(candidates)} candidates")
        print(f"Strategies used: {', '.join(results.get('strategies_tried', []))}")

        # Auto-download top result if requested
        if auto_download and candidates:
            print("\n🚀 Auto-downloading top result...")
            top_candidate = self._dict_to_candidate(candidates[0])
            return self._download_candidate(top_candidate)

        # Display candidates
        self._display_candidates(candidates[:10])

        # Interactive selection
        return self._interactive_select(candidates)

    def _display_candidates(self, candidates: List[Dict]):
        """Display candidate list in readable format"""
        print("\n" + "=" * 60)
        print("SEARCH RESULTS")
        print("=" * 60)

        for i, candidate in enumerate(candidates, 1):
            score = candidate.get("score", 0)
            confidence = candidate.get("confidence", "unknown")
            name = candidate.get("name", "Unknown")
            model_id = candidate.get("model_id", 0)
            creator = candidate.get("creator", "Unknown")

            # Confidence indicator
            if confidence == "high":
                indicator = "🟢"
            elif confidence == "medium":
                indicator = "🟡"
            else:
                indicator = "🔴"

            print(f"\n[{i}] {indicator} Score: {score} | Confidence: {confidence}")
            print(f"    Name: {name}")
            print(f"    ID: {model_id} | Creator: {creator}")
            print(f"    File: {candidate.get('filename', 'N/A')}")

    def _interactive_select(self, candidates: List[Dict]) -> SelectionResult:
        """
        Interactive selection prompt.

        Args:
            candidates: List of candidate dicts

        Returns:
            SelectionResult with user selection
        """
        print("\n" + "=" * 60)
        print("SELECT AN ACTION")
        print("=" * 60)
        print("Enter:")
        print("  - Number (1-10) to download that model")
        print("  - 'i' + number (e.g., 'i1') to view detailed info")
        print("  - 'q' to quit without downloading")
        print()

        while True:
            try:
                choice = input("Your choice: ").strip().lower()

                # Quit
                if choice == "q":
                    print("👋 Cancelled")
                    return SelectionResult(selected=False, action="cancel")

                # Info request
                if choice.startswith("i"):
                    try:
                        index = int(choice[1:]) - 1
                        if 0 <= index < len(candidates):
                            self._show_detailed_info(candidates[index])
                            continue
                        else:
                            print(f"❌ Invalid index. Choose 1-{min(len(candidates), 10)}")
                            continue
                    except (ValueError, IndexError):
                        print("❌ Invalid format. Use 'i' followed by number (e.g., 'i1')")
                        continue

                # Download selection
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(candidates):
                        candidate = self._dict_to_candidate(candidates[index])
                        return self._download_candidate(candidate)
                    else:
                        print(f"❌ Invalid choice. Choose 1-{min(len(candidates), 10)}")
                except ValueError:
                    print("❌ Invalid input. Enter a number, 'i' + number, or 'q'")

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                return SelectionResult(selected=False, action="cancel")

    def _show_detailed_info(self, candidate: Dict):
        """Show detailed information about a candidate"""
        print("\n" + "=" * 60)
        print("DETAILED INFORMATION")
        print("=" * 60)

        for key, value in candidate.items():
            if key != "metadata":
                print(f"{key}: {value}")

        if "metadata" in candidate and candidate["metadata"]:
            print("\nMetadata:")
            for key, value in candidate["metadata"].items():
                print(f"  {key}: {value}")

        print("=" * 60 + "\n")

    def _dict_to_candidate(self, candidate_dict: Dict) -> SearchCandidate:
        """Convert candidate dict to SearchCandidate object"""
        from .advanced_search import SearchStrategy, ConfidenceLevel

        return SearchCandidate(
            model_id=candidate_dict["model_id"],
            name=candidate_dict["name"],
            filename=candidate_dict["filename"],
            version_id=candidate_dict["version_id"],
            version_name=candidate_dict.get("version_name", ""),
            score=candidate_dict["score"],
            confidence=ConfidenceLevel(candidate_dict["confidence"]),
            found_by=SearchStrategy(candidate_dict["found_by"]),
            type=candidate_dict["type"],
            download_url=candidate_dict["download_url"],
            creator=candidate_dict.get("creator"),
            tag_used=candidate_dict.get("tag_used"),
            metadata=candidate_dict.get("metadata"),
        )

    def _download_candidate(self, candidate: SearchCandidate) -> SelectionResult:
        """Download the selected candidate"""
        print(f"\n📥 Downloading: {candidate.name}")
        print(f"   Model ID: {candidate.model_id}")
        print(f"   File: {candidate.filename}")
        print()

        result = self.downloader.download_by_id(candidate.model_id, candidate.version_id)

        return SelectionResult(selected=True, candidate=candidate, action="download")

    def batch_find(
        self, search_terms: List[str], model_type: str = "LORA", output_file: Optional[str] = None
    ) -> List[SelectionResult]:
        """
        Find and optionally download multiple models.

        Args:
            search_terms: List of search queries
            model_type: Model type filter
            output_file: Optional JSON file to save results

        Returns:
            List of SelectionResult objects
        """
        results = []

        for i, term in enumerate(search_terms, 1):
            print(f"\n{'=' * 60}")
            print(f"Query {i}/{len(search_terms)}: {term}")
            print("=" * 60)

            result = self.find_and_select(term, model_type, auto_download=False)
            results.append(result)

        # Export results if requested
        if output_file:
            self._export_results(results, output_file)

        return results

    def _export_results(self, results: List[SelectionResult], output_file: str):
        """Export search results to JSON"""
        export_data = []

        for result in results:
            if result.selected and result.candidate:
                export_data.append(result.candidate.to_dict())

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n📄 Results exported to: {output_file}")


def main():
    """CLI interface for standalone usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive fuzzy Civitai model finder")
    parser.add_argument("search_term", nargs="+", help="Model name(s) to search for")
    parser.add_argument("--type", default="LORA", help="Model type (default: LORA)")
    parser.add_argument(
        "--auto-download", action="store_true", help="Automatically download top result"
    )
    parser.add_argument("--batch", action="store_true", help="Process multiple search terms")
    parser.add_argument("--export", help="Export results to JSON file")

    args = parser.parse_args()

    finder = CivitaiFuzzyFinder()

    if args.batch:
        # Multiple searches
        finder.batch_find(args.search_term, args.type, args.export)
    else:
        # Single search
        search_term = " ".join(args.search_term)
        result = finder.find_and_select(search_term, args.type, args.auto_download)

        if not result.selected:
            exit(1)


if __name__ == "__main__":
    main()
