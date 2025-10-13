"""
Base Adapter Classes for ComfyFixerSmart

Provides abstract base classes and interfaces for adapters that integrate with
external systems like ComfyUI-Copilot. All adapters follow the adapter pattern
to provide clean boundaries between ComfyFixerSmart and external dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAdapter(ABC):
    """
    Abstract base class for all ComfyFixerSmart adapters.

    Adapters provide optional integration with external systems and features.
    All adapters must implement the common interface defined here.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize the adapter.

        Args:
            name: Unique identifier for this adapter
            description: Human-readable description of what this adapter does
        """
        self.name = name
        self.description = description
        self._initialized = False

    @abstractmethod
    def get_name(self) -> str:
        """
        Return the unique name/identifier for this adapter.

        Returns:
            Adapter name as string
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this adapter is available for use.

        This typically checks if required dependencies are installed
        and the underlying system is accessible.

        Returns:
            True if adapter is available, False otherwise
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the adapter for use.

        This method should perform any necessary setup, such as
        connecting to external services or loading configurations.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return a list of capabilities provided by this adapter.

        Returns:
            List of capability strings describing what this adapter can do
        """
        pass

    @abstractmethod
    def execute(self, operation: str, **kwargs) -> Any:
        """
        Execute an operation using this adapter.

        Args:
            operation: The operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            Operation result (type depends on the operation)

        Raises:
            NotImplementedError: If operation is not supported
            RuntimeError: If adapter is not initialized or operation fails
        """
        pass

    def is_initialized(self) -> bool:
        """
        Check if this adapter has been successfully initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def get_description(self) -> str:
        """
        Get the human-readable description of this adapter.

        Returns:
            Description string
        """
        return self.description

    def cleanup(self) -> None:
        """
        Clean up resources used by this adapter.

        This method should be called when the adapter is no longer needed.
        Default implementation does nothing - subclasses should override if needed.
        """
        pass


class CopilotAdapter(BaseAdapter):
    """
    Base class for adapters that integrate with ComfyUI-Copilot features.

    Provides common functionality for Copilot-based adapters, including
    dependency checking and graceful degradation.
    """

    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self.copilot_available = False

    def is_available(self) -> bool:
        """
        Check if ComfyUI-Copilot is available and this adapter can be used.

        Returns:
            True if Copilot is available, False otherwise
        """
        try:
            import comfyui_copilot  # type: ignore
            self.copilot_available = True
            return True
        except ImportError:
            self.copilot_available = False
            return False

    def initialize(self) -> bool:
        """
        Initialize the Copilot adapter.

        Returns:
            True if Copilot is available and initialization successful
        """
        if not self.is_available():
            return False

        # Perform Copilot-specific initialization here
        # Subclasses should override to add specific initialization logic
        self._initialized = True
        return True

    def get_capabilities(self) -> List[str]:
        """
        Return capabilities provided by this Copilot adapter.

        Returns:
            List of capability strings
        """
        if not self.copilot_available:
            return []

        # Subclasses should override to return actual capabilities
        return ["copilot_integration"]