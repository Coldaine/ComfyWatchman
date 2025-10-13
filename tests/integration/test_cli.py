"""
Integration tests for the CLI module.

Tests command-line interface functionality, argument parsing,
and integration with core components.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import pytest

from comfyfixersmart.cli import create_parser, main


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_create_parser_basic(self):
        """Test creating the basic argument parser."""
        parser = create_parser()

        assert parser is not None
        assert parser.prog == "comfyfixer"
        assert "ComfyFixerSmart" in parser.description

    def test_parser_with_workflow_files(self):
        """Test parsing workflow file arguments."""
        parser = create_parser()
        args = parser.parse_args(["workflow1.json", "workflow2.json"])

        assert args.workflows == ["workflow1.json", "workflow2.json"]
        assert args.workflow_dirs is None

    def test_parser_with_workflow_dirs(self):
        """Test parsing workflow directory arguments."""
        parser = create_parser()
        args = parser.parse_args(["--dir", "/workflows", "--workflow-dir", "/more_workflows"])

        assert args.workflow_dirs == ["/workflows", "/more_workflows"]
        assert args.workflows == []

    def test_parser_with_search_backends(self):
        """Test parsing search backend arguments."""
        parser = create_parser()
        args = parser.parse_args(["--search", "civitai,qwen"])

        assert args.search == "civitai,qwen"

    def test_parser_with_v1_mode(self):
        """Test parsing v1 compatibility mode."""
        parser = create_parser()
        args = parser.parse_args(["--v1"])

        assert args.v1 is True
        assert args.v2 is False

    def test_parser_with_v2_mode(self):
        """Test parsing v2 mode (default)."""
        parser = create_parser()
        args = parser.parse_args(["--v2"])

        assert args.v2 is True
        assert args.v1 is False

    def test_parser_with_output_dir(self):
        """Test parsing output directory argument."""
        parser = create_parser()
        args = parser.parse_args(["--output-dir", "/custom/output"])

        assert args.output_dir == "/custom/output"

    def test_parser_with_models_dir(self):
        """Test parsing models directory argument."""
        parser = create_parser()
        args = parser.parse_args(["--models-dir", "/custom/models"])

        assert args.models_dir == "/custom/models"

    def test_parser_with_scan_only(self):
        """Test parsing scan-only flag."""
        parser = create_parser()
        args = parser.parse_args(["--scan-only"])

        assert args.scan_only is True

    def test_parser_with_generate_scripts(self):
        """Test parsing generate-scripts flag."""
        parser = create_parser()
        args = parser.parse_args(["--generate-scripts"])

        assert args.generate_scripts is True

    def test_parser_with_verbose(self):
        """Test parsing verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["--verbose"])

        assert args.verbose is True

    def test_parser_help_output(self):
        """Test that help output is generated correctly."""
        parser = create_parser()

        # Capture help output
        help_output = parser.format_help()

        assert "ComfyFixerSmart" in help_output
        assert "workflow files" in help_output.lower()
        assert "examples:" in help_output.lower()


class TestCLIMainFunction:
    """Test the main CLI function."""

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_workflow_files(self, mock_run_comfy_fixer):
        """Test main function with workflow file arguments."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "workflow1.json", "workflow2.json"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        mock_run_comfy_fixer.assert_called_once()

        # Check call arguments
        call_args = mock_run_comfy_fixer.call_args
        assert call_args[1]["specific_workflows"] == ["workflow1.json", "workflow2.json"]

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_workflow_dirs(self, mock_run_comfy_fixer):
        """Test main function with workflow directory arguments."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "--dir", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        call_args = mock_run_comfy_fixer.call_args
        assert "/workflows" in call_args[1]["workflow_dirs"]

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_scan_only(self, mock_run_comfy_fixer):
        """Test main function with scan-only flag."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "--scan-only", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        call_args = mock_run_comfy_fixer.call_args
        assert call_args[1]["scan_only"] is True

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_generate_scripts(self, mock_run_comfy_fixer):
        """Test main function with generate-scripts flag."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "--generate-scripts", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        call_args = mock_run_comfy_fixer.call_args
        assert call_args[1]["generate_scripts"] is True

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_search_backends(self, mock_run_comfy_fixer):
        """Test main function with search backend specification."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "--search", "civitai,huggingface", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        call_args = mock_run_comfy_fixer.call_args
        assert call_args[1]["search_backends"] == ["civitai", "huggingface"]

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_v1_mode(self, mock_run_comfy_fixer):
        """Test main function with v1 compatibility mode."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "--v1", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        call_args = mock_run_comfy_fixer.call_args
        assert call_args[1]["v1_mode"] is True

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_with_v2_mode(self, mock_run_comfy_fixer):
        """Test main function with v2 mode."""
        mock_run_comfy_fixer.return_value = {"success": True}

        test_args = ["comfyfixer", "--v2", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        call_args = mock_run_comfy_fixer.call_args
        assert call_args[1]["v2_mode"] is True

    @patch('comfyfixersmart.cli.run_comfy_fixer')
    def test_main_error_handling(self, mock_run_comfy_fixer):
        """Test main function error handling."""
        mock_run_comfy_fixer.side_effect = Exception("Test error")

        test_args = ["comfyfixer", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 1  # Should return error code

    @patch('comfyfixersmart.cli.run_v1_compatibility_mode')
    def test_main_v1_mode_execution(self, mock_v1_mode):
        """Test that v1 mode calls the correct function."""
        mock_v1_mode.return_value = {"success": True}

        test_args = ["comfyfixer", "--v1", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        mock_v1_mode.assert_called_once()

    @patch('comfyfixersmart.cli.run_v2_compatibility_mode')
    def test_main_v2_mode_execution(self, mock_v2_mode):
        """Test that v2 mode calls the correct function."""
        mock_v2_mode.return_value = {"success": True}

        test_args = ["comfyfixer", "--v2", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        mock_v2_mode.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI with core functionality."""

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_core_integration(self, mock_core_class):
        """Test CLI integration with ComfyFixerCore."""
        mock_core = Mock()
        mock_core.run.return_value = {
            "run_id": "test_run_123",
            "workflows_scanned": 5,
            "models_found": 10,
            "models_resolved": 8,
            "downloads_generated": 2
        }
        mock_core_class.return_value = mock_core

        test_args = ["comfyfixer", "--scan-only", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0
        mock_core.run.assert_called_once()

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_with_multiple_directories(self, mock_core_class):
        """Test CLI with multiple workflow directories."""
        mock_core = Mock()
        mock_core.run.return_value = {"success": True}
        mock_core_class.return_value = mock_core

        test_args = [
            "comfyfixer",
            "--dir", "/workflows1",
            "--dir", "/workflows2",
            "--workflow-dir", "/workflows3"
        ]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0

        call_args = mock_core.run.call_args
        workflow_dirs = call_args[1]["workflow_dirs"]
        assert "/workflows1" in workflow_dirs
        assert "/workflows2" in workflow_dirs
        assert "/workflows3" in workflow_dirs

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_with_custom_output_dir(self, mock_core_class):
        """Test CLI with custom output directory."""
        mock_core = Mock()
        mock_core.run.return_value = {"success": True}
        mock_core_class.return_value = mock_core

        test_args = ["comfyfixer", "--output-dir", "/custom/output", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0

        call_args = mock_core.run.call_args
        assert call_args[1]["output_dir"] == "/custom/output"

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_with_custom_models_dir(self, mock_core_class):
        """Test CLI with custom models directory."""
        mock_core = Mock()
        mock_core.run.return_value = {"success": True}
        mock_core_class.return_value = mock_core

        test_args = ["comfyfixer", "--models-dir", "/custom/models", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0

        call_args = mock_core.run.call_args
        assert call_args[1]["models_dir"] == "/custom/models"

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_verbose_output(self, mock_core_class, capsys):
        """Test CLI verbose output."""
        mock_core = Mock()
        mock_core.run.return_value = {
            "run_id": "verbose_test_123",
            "workflows_scanned": 3,
            "models_found": 7,
            "models_resolved": 5
        }
        mock_core_class.return_value = mock_core

        test_args = ["comfyfixer", "--verbose", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 0

        # Capture output
        captured = capsys.readouterr()
        output = captured.out

        # Should contain run summary
        assert "verbose_test_123" in output or "3" in output

    def test_cli_invalid_arguments(self):
        """Test CLI with invalid arguments."""
        test_args = ["comfyfixer", "--invalid-flag"]
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with error code for invalid arguments
            assert exc_info.value.code == 2


class TestCLIScriptEntryPoints:
    """Test CLI script entry points."""

    @patch('comfyfixersmart.cli.main')
    def test_comfyfixer_script_entry(self, mock_main):
        """Test comfyfixer script entry point."""
        mock_main.return_value = 0

        # Import should work (this tests that the entry point is properly configured)
        try:
            import comfyfixersmart.cli
            assert hasattr(comfyfixersmart.cli, 'main')
        except ImportError:
            pytest.skip("CLI module not properly installed")

    @patch('comfyfixersmart.cli.main')
    def test_comfy_fixer_smart_script_entry(self, mock_main):
        """Test comfy-fixer-smart script entry point."""
        mock_main.return_value = 0

        # This would be tested by the actual entry point configuration
        # For now, just verify the main function exists
        from comfyfixersmart.cli import main as cli_main
        assert callable(cli_main)


class TestCLIErrorScenarios:
    """Test CLI error handling scenarios."""

    def test_cli_no_arguments_shows_help(self):
        """Test that running CLI with no arguments shows help."""
        test_args = ["comfyfixer"]
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 2 (argparse error for required arguments)
            assert exc_info.value.code == 2

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_core_initialization_failure(self, mock_core_class):
        """Test CLI when core initialization fails."""
        mock_core_class.side_effect = Exception("Core init failed")

        test_args = ["comfyfixer", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        assert exit_code == 1

    @patch('comfyfixersmart.cli.ComfyFixerCore')
    def test_cli_run_returns_error(self, mock_core_class):
        """Test CLI when core run returns error."""
        mock_core = Mock()
        mock_core.run.return_value = {"error": "Run failed"}
        mock_core_class.return_value = mock_core

        test_args = ["comfyfixer", "/workflows"]
        with patch('sys.argv', test_args):
            exit_code = main()

        # Should still return 0 since the run completed (even with error result)
        assert exit_code == 0