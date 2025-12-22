"""Unit tests for data_types.py multi-stage analysis dataclasses."""

import pytest
from pydantic import ValidationError
from adw_modules.data_types import (
    ComponentAnalysis,
    ComponentType,
    DRYFinding,
    DRYSeverity,
    ContextAnalysis,
    AnalysisScope,
    ADWStateData,
)


class TestComponentAnalysis:
    """Tests for ComponentAnalysis dataclass."""

    def test_valid_component_analysis(self):
        """Test creating valid ComponentAnalysis."""
        component = ComponentAnalysis(
            component_type=ComponentType.FRONTEND,
            complexity_score=0.5,
            dependencies=["react", "typescript"],
            lines_of_code=1000,
            file_count=10,
            reasoning="Component handles user authentication UI",
        )
        assert component.component_type == ComponentType.FRONTEND
        assert component.complexity_score == 0.5
        assert len(component.dependencies) == 2
        assert component.lines_of_code == 1000
        assert component.file_count == 10

    def test_invalid_component_type(self):
        """Test invalid component type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ComponentAnalysis(
                component_type="invalid_type",
                complexity_score=0.5,
                dependencies=[],
                lines_of_code=100,
                file_count=1,
                reasoning="test",
            )
        assert "component_type" in str(exc_info.value)

    def test_complexity_score_range_validation(self):
        """Test complexity score must be between 0.0 and 1.0."""
        # Valid boundaries
        ComponentAnalysis(
            component_type=ComponentType.BACKEND,
            complexity_score=0.0,
            dependencies=[],
            lines_of_code=50,
            file_count=1,
            reasoning="minimal component",
        )
        ComponentAnalysis(
            component_type=ComponentType.BACKEND,
            complexity_score=1.0,
            dependencies=[],
            lines_of_code=5000,
            file_count=50,
            reasoning="complex component",
        )

        # Invalid: below range
        with pytest.raises(ValidationError):
            ComponentAnalysis(
                component_type=ComponentType.BACKEND,
                complexity_score=-0.1,
                dependencies=[],
                lines_of_code=50,
                file_count=1,
                reasoning="test",
            )

        # Invalid: above range
        with pytest.raises(ValidationError):
            ComponentAnalysis(
                component_type=ComponentType.BACKEND,
                complexity_score=1.1,
                dependencies=[],
                lines_of_code=50,
                file_count=1,
                reasoning="test",
            )

    def test_empty_dependencies_list(self):
        """Test that empty dependencies list is valid."""
        component = ComponentAnalysis(
            component_type=ComponentType.UTILITY,
            complexity_score=0.2,
            dependencies=[],
            lines_of_code=50,
            file_count=1,
            reasoning="standalone utility",
        )
        assert component.dependencies == []

    def test_property_methods(self):
        """Test convenience property methods."""
        frontend = ComponentAnalysis(
            component_type=ComponentType.FRONTEND,
            complexity_score=0.5,
            dependencies=[],
            lines_of_code=100,
            file_count=5,
            reasoning="test",
        )
        assert frontend.is_frontend is True
        assert frontend.is_backend is False

        backend = ComponentAnalysis(
            component_type=ComponentType.BACKEND,
            complexity_score=0.7,
            dependencies=[],
            lines_of_code=200,
            file_count=8,
            reasoning="test",
        )
        assert backend.is_backend is True
        assert backend.is_frontend is False

    def test_serialization(self):
        """Test serialization via model_dump()."""
        component = ComponentAnalysis(
            component_type=ComponentType.API,
            complexity_score=0.6,
            dependencies=["fastapi", "pydantic"],
            lines_of_code=500,
            file_count=15,
            reasoning="REST API implementation",
        )
        data = component.model_dump()
        assert data["component_type"] == "api"
        assert data["complexity_score"] == 0.6
        assert data["dependencies"] == ["fastapi", "pydantic"]
        assert data["lines_of_code"] == 500
        assert data["file_count"] == 15

    def test_deserialization(self):
        """Test deserialization via model_validate()."""
        data = {
            "component_type": "database",
            "complexity_score": 0.8,
            "dependencies": ["sqlalchemy", "psycopg2"],
            "lines_of_code": 800,
            "file_count": 20,
            "reasoning": "Database layer implementation",
        }
        component = ComponentAnalysis.model_validate(data)
        assert component.component_type == ComponentType.DATABASE
        assert component.complexity_score == 0.8
        assert component.dependencies == ["sqlalchemy", "psycopg2"]

    def test_round_trip_serialization(self):
        """Test serialize → deserialize round-trip preserves data."""
        original = ComponentAnalysis(
            component_type=ComponentType.TEST,
            complexity_score=0.3,
            dependencies=["pytest", "coverage"],
            lines_of_code=300,
            file_count=12,
            reasoning="Test suite implementation",
        )
        data = original.model_dump()
        restored = ComponentAnalysis.model_validate(data)
        assert restored == original


class TestDRYFinding:
    """Tests for DRYFinding dataclass."""

    def test_valid_dry_finding(self):
        """Test creating valid DRYFinding."""
        finding = DRYFinding(
            severity=DRYSeverity.HIGH,
            pattern_description="Repeated authentication logic",
            occurrences=5,
            locations=["auth.py:100", "user.py:250", "api.py:75"],
            suggested_refactor="Extract to auth_utils.py",
            estimated_savings_loc=120,
        )
        assert finding.severity == DRYSeverity.HIGH
        assert finding.occurrences == 5
        assert len(finding.locations) == 3

    def test_invalid_severity(self):
        """Test invalid severity raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DRYFinding(
                severity="super_critical",
                pattern_description="test",
                occurrences=2,
                locations=["file.py:1"],
                estimated_savings_loc=10,
            )
        assert "severity" in str(exc_info.value)

    def test_occurrences_must_be_positive(self):
        """Test occurrences must be at least 1."""
        # Valid: 1 occurrence
        DRYFinding(
            severity=DRYSeverity.LOW,
            pattern_description="test",
            occurrences=1,
            locations=["file.py:1"],
            estimated_savings_loc=5,
        )

        # Invalid: 0 occurrences
        with pytest.raises(ValidationError):
            DRYFinding(
                severity=DRYSeverity.LOW,
                pattern_description="test",
                occurrences=0,
                locations=[],
                estimated_savings_loc=0,
            )

        # Invalid: negative occurrences
        with pytest.raises(ValidationError):
            DRYFinding(
                severity=DRYSeverity.LOW,
                pattern_description="test",
                occurrences=-1,
                locations=[],
                estimated_savings_loc=0,
            )

    def test_optional_suggested_refactor(self):
        """Test suggested_refactor is optional."""
        finding = DRYFinding(
            severity=DRYSeverity.MEDIUM,
            pattern_description="Duplicate validation",
            occurrences=3,
            locations=["a.py:10", "b.py:20"],
            estimated_savings_loc=30,
        )
        assert finding.suggested_refactor is None

    def test_property_methods(self):
        """Test severity property methods."""
        critical = DRYFinding(
            severity=DRYSeverity.CRITICAL,
            pattern_description="test",
            occurrences=10,
            locations=["file.py:1"],
            estimated_savings_loc=500,
        )
        assert critical.is_critical is True
        assert critical.is_high is False

        high = DRYFinding(
            severity=DRYSeverity.HIGH,
            pattern_description="test",
            occurrences=5,
            locations=["file.py:1"],
            estimated_savings_loc=100,
        )
        assert high.is_high is True
        assert high.is_critical is False

    def test_serialization(self):
        """Test serialization via model_dump()."""
        finding = DRYFinding(
            severity=DRYSeverity.MEDIUM,
            pattern_description="Repeated error handling",
            occurrences=4,
            locations=["handler1.py:50", "handler2.py:75"],
            suggested_refactor="Create error_handler_utils.py",
            estimated_savings_loc=80,
        )
        data = finding.model_dump()
        assert data["severity"] == "medium"
        assert data["pattern_description"] == "Repeated error handling"
        assert data["occurrences"] == 4
        assert len(data["locations"]) == 2

    def test_deserialization(self):
        """Test deserialization via model_validate()."""
        data = {
            "severity": "low",
            "pattern_description": "Minor duplication",
            "occurrences": 2,
            "locations": ["a.py:10"],
            "estimated_savings_loc": 15,
        }
        finding = DRYFinding.model_validate(data)
        assert finding.severity == DRYSeverity.LOW
        assert finding.occurrences == 2

    def test_round_trip_serialization(self):
        """Test serialize → deserialize round-trip preserves data."""
        original = DRYFinding(
            severity=DRYSeverity.CRITICAL,
            pattern_description="Critical duplication",
            occurrences=8,
            locations=["x.py:100", "y.py:200", "z.py:300"],
            suggested_refactor="Extract to shared module",
            estimated_savings_loc=400,
        )
        data = original.model_dump()
        restored = DRYFinding.model_validate(data)
        assert restored == original


class TestContextAnalysis:
    """Tests for ContextAnalysis dataclass."""

    def test_valid_context_analysis(self):
        """Test creating valid ContextAnalysis."""
        analysis = ContextAnalysis(
            scope=AnalysisScope.SUBSYSTEM,
            affected_files=["file1.py", "file2.py", "file3.py"],
            integration_points=["API Gateway", "Database Layer"],
            risk_assessment="Medium risk - requires integration testing",
            test_coverage_required=True,
            estimated_impact_loc=250,
        )
        assert analysis.scope == AnalysisScope.SUBSYSTEM
        assert len(analysis.affected_files) == 3
        assert analysis.test_coverage_required is True

    def test_invalid_scope(self):
        """Test invalid scope raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ContextAnalysis(
                scope="global",
                affected_files=[],
                integration_points=[],
                risk_assessment="test",
                test_coverage_required=False,
                estimated_impact_loc=10,
            )
        assert "scope" in str(exc_info.value)

    def test_empty_lists_valid(self):
        """Test empty affected_files and integration_points lists are valid."""
        analysis = ContextAnalysis(
            scope=AnalysisScope.FILE,
            affected_files=[],
            integration_points=[],
            risk_assessment="Low risk - isolated change",
            test_coverage_required=False,
            estimated_impact_loc=5,
        )
        assert analysis.affected_files == []
        assert analysis.integration_points == []

    def test_property_methods(self):
        """Test scope property methods."""
        system = ContextAnalysis(
            scope=AnalysisScope.SYSTEM,
            affected_files=["many", "files", "here"],
            integration_points=["API", "DB", "Cache"],
            risk_assessment="High risk",
            test_coverage_required=True,
            estimated_impact_loc=1000,
        )
        assert system.is_system_wide is True
        assert system.requires_integration_tests is True

        file_scope = ContextAnalysis(
            scope=AnalysisScope.FILE,
            affected_files=["single.py"],
            integration_points=[],
            risk_assessment="Low risk",
            test_coverage_required=False,
            estimated_impact_loc=10,
        )
        assert file_scope.is_system_wide is False
        assert file_scope.requires_integration_tests is False

        subsystem = ContextAnalysis(
            scope=AnalysisScope.SUBSYSTEM,
            affected_files=["a.py", "b.py"],
            integration_points=["API"],
            risk_assessment="Medium risk",
            test_coverage_required=True,
            estimated_impact_loc=100,
        )
        assert subsystem.requires_integration_tests is True

    def test_serialization(self):
        """Test serialization via model_dump()."""
        analysis = ContextAnalysis(
            scope=AnalysisScope.MODULE,
            affected_files=["module_a.py", "module_b.py"],
            integration_points=["Service Layer"],
            risk_assessment="Medium risk - module-wide changes",
            test_coverage_required=True,
            estimated_impact_loc=150,
        )
        data = analysis.model_dump()
        assert data["scope"] == "module"
        assert len(data["affected_files"]) == 2
        assert data["test_coverage_required"] is True

    def test_deserialization(self):
        """Test deserialization via model_validate()."""
        data = {
            "scope": "system",
            "affected_files": ["f1.py", "f2.py", "f3.py"],
            "integration_points": ["API", "DB"],
            "risk_assessment": "High risk",
            "test_coverage_required": True,
            "estimated_impact_loc": 500,
        }
        analysis = ContextAnalysis.model_validate(data)
        assert analysis.scope == AnalysisScope.SYSTEM
        assert len(analysis.affected_files) == 3

    def test_round_trip_serialization(self):
        """Test serialize → deserialize round-trip preserves data."""
        original = ContextAnalysis(
            scope=AnalysisScope.FILE,
            affected_files=["single_file.py"],
            integration_points=[],
            risk_assessment="Low risk - isolated file change",
            test_coverage_required=False,
            estimated_impact_loc=25,
        )
        data = original.model_dump()
        restored = ContextAnalysis.model_validate(data)
        assert restored == original


class TestADWStateDataExtensions:
    """Tests for ADWStateData with multi-stage analysis fields."""

    def test_state_without_analysis_fields(self):
        """Test backward compatibility - state without analysis fields."""
        state = ADWStateData(adw_id="test-123")
        assert state.adw_id == "test-123"
        assert state.component_analysis is None
        assert state.dry_findings is None
        assert state.context_analysis is None
        assert state.multi_stage_metadata is None

    def test_state_with_component_analysis(self):
        """Test state with component_analysis field."""
        component = ComponentAnalysis(
            component_type=ComponentType.BACKEND,
            complexity_score=0.7,
            dependencies=["fastapi"],
            lines_of_code=500,
            file_count=10,
            reasoning="Backend API implementation",
        )
        state = ADWStateData(adw_id="test-456", component_analysis=component)
        assert state.component_analysis is not None
        assert state.component_analysis.component_type == ComponentType.BACKEND

    def test_state_with_dry_findings(self):
        """Test state with dry_findings list."""
        findings = [
            DRYFinding(
                severity=DRYSeverity.HIGH,
                pattern_description="Auth duplication",
                occurrences=3,
                locations=["a.py:10", "b.py:20"],
                estimated_savings_loc=50,
            ),
            DRYFinding(
                severity=DRYSeverity.MEDIUM,
                pattern_description="Validation duplication",
                occurrences=2,
                locations=["x.py:30"],
                estimated_savings_loc=20,
            ),
        ]
        state = ADWStateData(adw_id="test-789", dry_findings=findings)
        assert state.dry_findings is not None
        assert len(state.dry_findings) == 2
        assert state.dry_findings[0].severity == DRYSeverity.HIGH

    def test_state_with_context_analysis(self):
        """Test state with context_analysis field."""
        context = ContextAnalysis(
            scope=AnalysisScope.SYSTEM,
            affected_files=["file1.py", "file2.py"],
            integration_points=["API", "DB"],
            risk_assessment="High risk",
            test_coverage_required=True,
            estimated_impact_loc=300,
        )
        state = ADWStateData(adw_id="test-999", context_analysis=context)
        assert state.context_analysis is not None
        assert state.context_analysis.scope == AnalysisScope.SYSTEM

    def test_state_with_multi_stage_metadata(self):
        """Test state with multi_stage_metadata dict."""
        metadata = {
            "analysis_version": "1.0",
            "timestamp": "2025-12-22T10:00:00Z",
            "analyzer_agent": "complexity_analyzer",
        }
        state = ADWStateData(adw_id="test-meta", multi_stage_metadata=metadata)
        assert state.multi_stage_metadata is not None
        assert state.multi_stage_metadata["analysis_version"] == "1.0"

    def test_state_serialization_with_analysis_fields(self):
        """Test serialization of state with all analysis fields."""
        component = ComponentAnalysis(
            component_type=ComponentType.FRONTEND,
            complexity_score=0.5,
            dependencies=["react"],
            lines_of_code=200,
            file_count=5,
            reasoning="UI component",
        )
        findings = [
            DRYFinding(
                severity=DRYSeverity.LOW,
                pattern_description="Minor duplication",
                occurrences=2,
                locations=["a.py:1"],
                estimated_savings_loc=10,
            )
        ]
        context = ContextAnalysis(
            scope=AnalysisScope.MODULE,
            affected_files=["module.py"],
            integration_points=[],
            risk_assessment="Low risk",
            test_coverage_required=False,
            estimated_impact_loc=20,
        )
        state = ADWStateData(
            adw_id="test-full",
            component_analysis=component,
            dry_findings=findings,
            context_analysis=context,
            multi_stage_metadata={"test": "data"},
        )
        data = state.model_dump()
        assert "component_analysis" in data
        assert "dry_findings" in data
        assert "context_analysis" in data
        assert "multi_stage_metadata" in data
        assert data["component_analysis"]["component_type"] == "frontend"

    def test_state_deserialization_with_missing_fields(self):
        """Test loading state from JSON with missing analysis fields defaults to None."""
        data = {"adw_id": "test-minimal"}
        state = ADWStateData.model_validate(data)
        assert state.adw_id == "test-minimal"
        assert state.component_analysis is None
        assert state.dry_findings is None
        assert state.context_analysis is None

    def test_state_round_trip_with_all_fields(self):
        """Test full round-trip with all analysis fields populated."""
        original = ADWStateData(
            adw_id="round-trip-test",
            issue_number="123",
            branch_name="feature/test",
            component_analysis=ComponentAnalysis(
                component_type=ComponentType.API,
                complexity_score=0.8,
                dependencies=["fastapi"],
                lines_of_code=600,
                file_count=15,
                reasoning="REST API",
            ),
            dry_findings=[
                DRYFinding(
                    severity=DRYSeverity.CRITICAL,
                    pattern_description="Critical dup",
                    occurrences=5,
                    locations=["a.py:1"],
                    estimated_savings_loc=100,
                )
            ],
            context_analysis=ContextAnalysis(
                scope=AnalysisScope.SUBSYSTEM,
                affected_files=["a.py", "b.py"],
                integration_points=["API"],
                risk_assessment="Medium",
                test_coverage_required=True,
                estimated_impact_loc=150,
            ),
            multi_stage_metadata={"version": "2.0"},
        )
        data = original.model_dump()
        restored = ADWStateData.model_validate(data)
        assert restored.adw_id == original.adw_id
        assert restored.component_analysis.component_type == ComponentType.API
        assert len(restored.dry_findings) == 1
        assert restored.context_analysis.scope == AnalysisScope.SUBSYSTEM
        assert restored.multi_stage_metadata["version"] == "2.0"
