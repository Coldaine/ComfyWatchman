"""
Civitai Tools - Python Implementation

Complete Python ports of bash tools for Civitai model search and download.
MCP-ready architecture for integration with Claude Desktop and AI agents.
"""

from .advanced_search import (
    AdvancedCivitaiSearch,
    SearchCandidate,
    SearchStrategy,
    ConfidenceLevel,
    ModelScorer,
    TagExtractor,
    KnownModelsDB
)

from .direct_downloader import (
    CivitaiDirectDownloader,
    DownloadResult,
    DownloadStatus
)

from .search_diagnostics import (
    CivitaiSearchDebugger,
    SearchDiagnostic,
    DiagnosticLevel,
    DiagnosticMessage
)

from .batch_downloader import (
    CivitaiBatchDownloader,
    BatchJob,
    BatchSummary,
    BatchStatus
)

from .fuzzy_finder import (
    CivitaiFuzzyFinder,
    SelectionResult
)

__all__ = [
    # Main classes
    'AdvancedCivitaiSearch',
    'CivitaiDirectDownloader',
    'CivitaiSearchDebugger',
    'CivitaiBatchDownloader',
    'CivitaiFuzzyFinder',

    # Search types
    'SearchCandidate',
    'SearchStrategy',
    'ConfidenceLevel',

    # Download types
    'DownloadResult',
    'DownloadStatus',

    # Diagnostic types
    'SearchDiagnostic',
    'DiagnosticLevel',
    'DiagnosticMessage',

    # Batch types
    'BatchJob',
    'BatchSummary',
    'BatchStatus',

    # Selection types
    'SelectionResult',

    # Utility classes
    'ModelScorer',
    'TagExtractor',
    'KnownModelsDB',
]

__version__ = '1.0.0'
__author__ = 'ComfyWatchman Team'
__description__ = 'Python tools for Civitai model search and download'
