"""Tests for state validator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import tempfile
import shutil
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

from adws.utils.state_validator import StateValidator, ValidationResult


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_bool_true(self):
        """ValidationResult should be truthy when valid."""
        valid = ValidationResult(is_valid=True, errors=[], warnings=[])
        assert bool(valid) is True
        assert valid.is_valid is True
        assert len(valid.errors) == 0
        assert len(valid.warnings) == 0

    def test_validation_result_bool_false(self):
        """ValidationResult should be falsy when invalid."""
        invalid = ValidationResult(is_valid=False, errors=['Error'], warnings=[])
        assert bool(invalid) is False
        assert invalid.is_valid is False
        assert len(invalid.errors) == 1
        assert invalid.errors[0] == 'Error'

    def test_validation_result_with_warnings(self):
        """ValidationResult can have warnings even when valid."""
        result = ValidationResult(is_valid=True, errors=[], warnings=['Warning'])
        assert bool(result) is True
        assert len(result.warnings) == 1
        assert result.warnings[0] == 'Warning'


class TestStateValidatorInit:
    """Tests for StateValidator initialization."""

    def test_unknown_phase_raises_error(self):
        """Should raise error for unknown phase."""
        with pytest.raises(ValueError, match="Unknown phase"):
            StateValidator(phase='invalid_phase')

    def test_valid_phase_plan(self):
        """Should initialize with valid phase 'plan'."""
        validator = StateValidator(phase='plan')
        assert validator.phase == 'plan'
        assert 'requires' in validator.contract
        assert 'produces' in validator.contract

    def test_valid_phase_test(self):
        """Should initialize with valid phase 'test'."""
        validator = StateValidator(phase='test')
        assert validator.phase == 'test'
        assert 'test_files' in validator.contract['requires']

    def test_all_phases_supported(self):
        """All 10 phases should be supported."""
        phases = ['plan', 'validate', 'build', 'lint', 'test',
                 'review', 'document', 'ship', 'cleanup', 'verify']

        for phase in phases:
            validator = StateValidator(phase=phase)
            assert validator.phase == phase


class TestPlanPhaseValidation:
    """Tests for Plan phase validation."""

    @patch('adws.utils.state_validator.os.environ.get')
    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_plan_inputs_valid(self, mock_repo_class, mock_env_get):
        """Plan phase with valid inputs should pass."""
        # Mock environment
        mock_env_get.return_value = 'fake_github_token'

        # Mock database workflow
        mock_workflow = Mock()
        mock_workflow.issue_number = 123
        mock_workflow.adw_id = '77c90e61'

        mock_repo = Mock()
        mock_repo.find_by_issue_number.return_value = mock_workflow
        mock_repo_class.return_value = mock_repo

        validator = StateValidator(phase='plan')
        result = validator.validate_inputs(123)

        assert result.is_valid is True
        assert len(result.errors) == 0

    @patch('adws.utils.state_validator.os.environ.get')
    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_plan_inputs_missing_github_token(self, mock_repo_class, mock_env_get):
        """Plan phase without GitHub token should fail."""
        # No GitHub token
        mock_env_get.return_value = None

        # Mock database workflow
        mock_workflow = Mock()
        mock_workflow.issue_number = 123
        mock_workflow.adw_id = None

        mock_repo = Mock()
        mock_repo.find_by_issue_number.return_value = mock_workflow
        mock_repo_class.return_value = mock_repo

        validator = StateValidator(phase='plan')
        result = validator.validate_inputs(123)

        assert result.is_valid is False
        assert any('GITHUB_TOKEN' in error for error in result.errors)

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_plan_inputs_workflow_not_found(self, mock_repo_class):
        """Plan phase without workflow should fail."""
        mock_repo = Mock()
        mock_repo.find_by_issue_number.return_value = None
        mock_repo_class.return_value = mock_repo

        validator = StateValidator(phase='plan')
        result = validator.validate_inputs(123)

        assert result.is_valid is False
        assert any('Workflow not found' in error for error in result.errors)

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_plan_outputs_valid(self, mock_repo_class):
        """Plan phase with valid outputs should pass."""
        # Create temporary worktree
        temp_dir = tempfile.mkdtemp()

        try:
            # Create required files
            state_file = Path(temp_dir) / 'adw_state.json'
            state_file.write_text(json.dumps({
                'adw_id': '77c90e61',
                'plan_file': str(Path(temp_dir) / 'specs' / 'plan.md'),
                'worktree_path': temp_dir
            }))

            # Create plan file
            specs_dir = Path(temp_dir) / 'specs'
            specs_dir.mkdir()
            plan_file = specs_dir / 'plan.md'
            plan_file.write_text('# Plan\n\nDetailed plan content here...' * 10)  # Make it > 100 bytes

            # Mock database workflow
            mock_workflow = Mock()
            mock_workflow.issue_number = 123
            mock_workflow.adw_id = '77c90e61'

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            # Mock worktree path resolution
            validator = StateValidator(phase='plan')
            validator._get_worktree_path = Mock(return_value=temp_dir)

            result = validator.validate_outputs(123)

            assert result.is_valid is True
            assert len(result.errors) == 0

        finally:
            shutil.rmtree(temp_dir)


class TestTestPhaseValidation:
    """Tests for Test phase validation."""

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_test_inputs_missing_worktree(self, mock_repo_class):
        """Test phase without worktree should fail."""
        mock_workflow = Mock()
        mock_workflow.issue_number = 123
        mock_workflow.adw_id = '77c90e61'

        mock_repo = Mock()
        mock_repo.find_by_issue_number.return_value = mock_workflow
        mock_repo_class.return_value = mock_repo

        validator = StateValidator(phase='test')
        validator._get_worktree_path = Mock(return_value=None)

        result = validator.validate_inputs(123)

        assert result.is_valid is False
        assert any('worktree' in error.lower() for error in result.errors)

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_test_inputs_missing_test_files(self, mock_repo_class):
        """Test phase without test files should fail."""
        # Create temp directory without test files
        temp_dir = tempfile.mkdtemp()

        try:
            # Create worktree structure but no tests
            app_dir = Path(temp_dir) / 'app'
            app_dir.mkdir()
            (app_dir / 'server').mkdir()
            (app_dir / 'client').mkdir()

            mock_workflow = Mock()
            mock_workflow.issue_number = 123
            mock_workflow.adw_id = '77c90e61'

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            validator = StateValidator(phase='test')
            validator._get_worktree_path = Mock(return_value=temp_dir)

            result = validator.validate_inputs(123)

            assert result.is_valid is False
            assert any('test files' in error.lower() for error in result.errors)

        finally:
            shutil.rmtree(temp_dir)

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_test_inputs_with_test_files(self, mock_repo_class):
        """Test phase with test files should pass."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Create worktree with test files
            tests_dir = Path(temp_dir) / 'app' / 'server' / 'tests'
            tests_dir.mkdir(parents=True)
            (tests_dir / 'test_example.py').write_text('def test_example(): pass')

            state_file = Path(temp_dir) / 'adw_state.json'
            state_file.write_text(json.dumps({'worktree_path': temp_dir}))

            mock_workflow = Mock()
            mock_workflow.issue_number = 123
            mock_workflow.adw_id = '77c90e61'

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            validator = StateValidator(phase='test')
            validator._get_worktree_path = Mock(return_value=temp_dir)

            result = validator.validate_inputs(123)

            assert result.is_valid is True
            assert len(result.errors) == 0

        finally:
            shutil.rmtree(temp_dir)


class TestBuildPhaseValidation:
    """Tests for Build phase validation."""

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_build_inputs_missing_plan_file(self, mock_repo_class):
        """Build phase without plan file should fail."""
        temp_dir = tempfile.mkdtemp()

        try:
            state_file = Path(temp_dir) / 'adw_state.json'
            state_file.write_text(json.dumps({
                'worktree_path': temp_dir,
                'branch_name': 'feature/test'
                # Missing plan_file
            }))

            mock_workflow = Mock()
            mock_workflow.issue_number = 123
            mock_workflow.adw_id = '77c90e61'

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            validator = StateValidator(phase='build')
            validator._get_worktree_path = Mock(return_value=temp_dir)

            result = validator.validate_inputs(123)

            assert result.is_valid is False
            assert any('plan_file' in error for error in result.errors)

        finally:
            shutil.rmtree(temp_dir)


class TestShipPhaseValidation:
    """Tests for Ship phase validation."""

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_ship_inputs_missing_required_fields(self, mock_repo_class):
        """Ship phase with missing required fields should fail."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Incomplete state
            state_file = Path(temp_dir) / 'adw_state.json'
            state_file.write_text(json.dumps({
                'adw_id': '77c90e61',
                'branch_name': 'feature/test'
                # Missing: plan_file, issue_class, worktree_path, backend_port, frontend_port
            }))

            mock_workflow = Mock()
            mock_workflow.issue_number = 123
            mock_workflow.adw_id = '77c90e61'

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            validator = StateValidator(phase='ship')
            validator._get_worktree_path = Mock(return_value=temp_dir)

            result = validator.validate_inputs(123)

            assert result.is_valid is False
            assert any('Missing required state fields' in error for error in result.errors)

        finally:
            shutil.rmtree(temp_dir)


class TestWorktreePathResolution:
    """Tests for worktree path resolution."""

    def test_get_worktree_path_found(self):
        """Should find worktree at expected path."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Create trees directory
            trees_dir = Path(temp_dir) / 'trees'
            trees_dir.mkdir()

            worktree_dir = trees_dir / '77c90e61'
            worktree_dir.mkdir()

            validator = StateValidator(phase='plan')

            # Patch Path to use temp directory
            with patch('adws.utils.state_validator.Path') as mock_path:
                def path_side_effect(path_str):
                    if path_str.startswith('trees/'):
                        return Path(temp_dir) / path_str
                    return Path(path_str)

                mock_path.side_effect = path_side_effect

                result = validator._get_worktree_path('77c90e61')
                # Should find it (after patching)

        finally:
            shutil.rmtree(temp_dir)

    def test_get_worktree_path_not_found(self):
        """Should return None if worktree doesn't exist."""
        validator = StateValidator(phase='plan')
        result = validator._get_worktree_path('nonexistent')
        assert result is None


class TestDatabaseIntegration:
    """Tests for database integration scenarios."""

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_database_error_handling(self, mock_repo_class):
        """Should handle database errors gracefully."""
        mock_repo = Mock()
        mock_repo.find_by_issue_number.side_effect = Exception("Database connection failed")
        mock_repo_class.return_value = mock_repo

        validator = StateValidator(phase='plan')
        result = validator.validate_inputs(123)

        assert result.is_valid is False
        assert any('Failed to query database' in error for error in result.errors)


class TestValidationWarnings:
    """Tests for validation warnings."""

    @patch('app.server.repositories.phase_queue_repository.PhaseQueueRepository')
    def test_state_file_load_failure_warning(self, mock_repo_class):
        """Failed state file load should create warning."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Create invalid JSON file
            state_file = Path(temp_dir) / 'adw_state.json'
            state_file.write_text('invalid json{{{')

            mock_workflow = Mock()
            mock_workflow.issue_number = 123
            mock_workflow.adw_id = '77c90e61'

            mock_repo = Mock()
            mock_repo.find_by_issue_number.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            validator = StateValidator(phase='test')
            validator._get_worktree_path = Mock(return_value=temp_dir)

            result = validator.validate_inputs(123)

            # Should have warnings about failed state load
            assert len(result.warnings) > 0

        finally:
            shutil.rmtree(temp_dir)
