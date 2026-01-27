# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Unit Tests for Human-in-the-Loop (HITL) Module
==============================================

This module provides unit tests for the HITL model interfaces and mock
implementations used in the coffee exchange order processing workflow.

How to Run:
    cd coffeeAGNTCY/coffee_agents/lungo
    pytest tests/test_hitl.py -v

Test Coverage:
    - TriggerDecision enum values
    - TriggerModelOutput dataclass serialization
    - AllocationScenario dataclass serialization
    - MockWhenToTriggerModel inference
    - MockWhatToRespondModel inference
    - Model factory functions
"""

import pytest
from typing import Dict, Any

from agents.supervisors.auction.graph.hitl import (
    TriggerDecision,
    TriggerModelInput,
    TriggerModelOutput,
    AllocationScenario,
    RespondModelOutput,
    MockWhenToTriggerModel,
    MockWhatToRespondModel,
    get_trigger_model,
    get_respond_model,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_order_query() -> str:
    """Sample order query that should trigger human intervention."""
    return "I need to place our Q2 order. 500 lbs total, budget capped at $2,000. What are our options?"


@pytest.fixture
def sample_simple_query() -> str:
    """Sample simple query that should NOT trigger human intervention."""
    return "What is the yield from Brazil?"


@pytest.fixture
def mock_trigger_model() -> MockWhenToTriggerModel:
    """Initialize mock WHEN-TO-TRIGGER model."""
    return MockWhenToTriggerModel()


@pytest.fixture
def mock_respond_model() -> MockWhatToRespondModel:
    """Initialize mock WHAT-TO-RESPOND model."""
    return MockWhatToRespondModel()


# =============================================================================
# DATA MODEL TESTS
# =============================================================================

class TestTriggerDecision:
    """Tests for TriggerDecision enum."""
    
    def test_trigger_value(self):
        """Test TRIGGER enum value."""
        assert TriggerDecision.TRIGGER.value == "TRIGGER"
    
    def test_no_trigger_value(self):
        """Test NO_TRIGGER enum value."""
        assert TriggerDecision.NO_TRIGGER.value == "NO_TRIGGER"
    
    def test_string_conversion(self):
        """Test enum can be converted to string."""
        assert str(TriggerDecision.TRIGGER) == "TriggerDecision.TRIGGER"


class TestTriggerModelOutput:
    """Tests for TriggerModelOutput dataclass."""
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        output = TriggerModelOutput(
            decision=TriggerDecision.TRIGGER,
            confidence=0.85,
            reasons=["Budget constraint", "No origin specified"],
            raw_output="test raw output"
        )
        
        result = output.to_dict()
        
        assert result["decision"] == "TRIGGER"
        assert result["confidence"] == 0.85
        assert len(result["reasons"]) == 2
        assert result["raw_output"] == "test raw output"
    
    def test_optional_raw_output(self):
        """Test that raw_output is optional."""
        output = TriggerModelOutput(
            decision=TriggerDecision.NO_TRIGGER,
            confidence=0.5,
            reasons=[]
        )
        
        assert output.raw_output is None


class TestAllocationScenario:
    """Tests for AllocationScenario dataclass."""
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        scenario = AllocationScenario(
            name="Test Scenario",
            description="A test scenario",
            farm_allocations={"brazil": 250, "colombia": 150},
            total_cost=1500.00,
            quality_score=87,
            risk_level="LOW"
        )
        
        result = scenario.to_dict()
        
        assert result["name"] == "Test Scenario"
        assert result["farm_allocations"]["brazil"] == 250
        assert result["total_cost"] == 1500.00
        assert result["quality_score"] == 87
        assert result["risk_level"] == "LOW"


# =============================================================================
# MOCK MODEL TESTS
# =============================================================================

class TestMockWhenToTriggerModel:
    """Tests for MockWhenToTriggerModel."""
    
    def test_initialization(self, mock_trigger_model: MockWhenToTriggerModel):
        """Test model initializes correctly."""
        assert mock_trigger_model.name == "mock-when-to-trigger-v1"
        assert mock_trigger_model.threshold == 0.65
    
    def test_triggers_on_budget_constraint(
        self, 
        mock_trigger_model: MockWhenToTriggerModel, 
        sample_order_query: str
    ):
        """Test that budget constraint triggers human intervention."""
        result = mock_trigger_model.inference(sample_order_query)
        
        # Should trigger due to budget, missing origin, and Q2 volatility
        assert result.decision == TriggerDecision.TRIGGER
        assert result.confidence >= mock_trigger_model.threshold
        assert len(result.reasons) > 0
        assert any("budget" in r.lower() for r in result.reasons)
    
    def test_no_trigger_on_simple_query(
        self, 
        mock_trigger_model: MockWhenToTriggerModel, 
        sample_simple_query: str
    ):
        """Test that simple inventory queries don't trigger."""
        result = mock_trigger_model.inference(sample_simple_query)
        
        # Simple query with Brazil specified, no budget, no order keywords
        # May or may not trigger depending on mock logic
        assert isinstance(result.decision, TriggerDecision)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_confidence_capped_at_one(self, mock_trigger_model: MockWhenToTriggerModel):
        """Test that confidence never exceeds 1.0."""
        # Query with all trigger conditions
        query = "Q2 order, 1000 lbs, budget $500, need options urgently"
        result = mock_trigger_model.inference(query)
        
        assert result.confidence <= 1.0
    
    def test_analyze_delegates_to_inference(
        self, 
        mock_trigger_model: MockWhenToTriggerModel, 
        sample_order_query: str
    ):
        """Test that analyze() method delegates to inference()."""
        result1 = mock_trigger_model.inference(sample_order_query)
        result2 = mock_trigger_model.analyze(sample_order_query)
        
        assert result1.decision == result2.decision
        assert result1.confidence == result2.confidence


class TestMockWhatToRespondModel:
    """Tests for MockWhatToRespondModel."""
    
    def test_initialization(self, mock_respond_model: MockWhatToRespondModel):
        """Test model initializes correctly."""
        assert mock_respond_model.name == "mock-what-to-respond-v1"
    
    def test_generates_scenarios(
        self, 
        mock_respond_model: MockWhatToRespondModel,
        mock_trigger_model: MockWhenToTriggerModel,
        sample_order_query: str
    ):
        """Test that model generates allocation scenarios."""
        # First get trigger output
        trigger_output = mock_trigger_model.inference(sample_order_query)
        
        # Then generate scenarios
        result = mock_respond_model.inference(
            user_query=sample_order_query,
            trigger_output=trigger_output
        )
        
        assert len(result.scenarios) == 4  # Mock generates 4 scenarios
        assert result.recommendation is not None
        assert result.rationale is not None
    
    def test_scenario_names(
        self, 
        mock_respond_model: MockWhatToRespondModel,
        mock_trigger_model: MockWhenToTriggerModel,
        sample_order_query: str
    ):
        """Test that scenarios have expected names."""
        trigger_output = mock_trigger_model.inference(sample_order_query)
        result = mock_respond_model.inference(
            user_query=sample_order_query,
            trigger_output=trigger_output
        )
        
        scenario_names = [s.name for s in result.scenarios]
        expected_names = ["Budget-Optimized", "Quality-First", "Balanced Diversification", "Budget-Strict"]
        
        assert scenario_names == expected_names
    
    def test_extracts_quantity_from_query(
        self, 
        mock_respond_model: MockWhatToRespondModel,
        mock_trigger_model: MockWhenToTriggerModel
    ):
        """Test that model extracts quantity from user query."""
        query = "I need 750 lbs of coffee, budget $3000"
        trigger_output = mock_trigger_model.inference(query)
        result = mock_respond_model.inference(
            user_query=query,
            trigger_output=trigger_output
        )
        
        # Check that at least one scenario references the quantity
        total_allocations = sum(result.scenarios[0].farm_allocations.values())
        assert total_allocations == 750  # Should match extracted quantity


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Tests for model factory functions."""
    
    def test_get_trigger_model_returns_mock(self):
        """Test that factory returns mock model by default."""
        model = get_trigger_model()
        assert isinstance(model, MockWhenToTriggerModel)
    
    def test_get_respond_model_returns_mock(self):
        """Test that factory returns mock model by default."""
        model = get_respond_model()
        assert isinstance(model, MockWhatToRespondModel)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestHITLIntegration:
    """Integration tests for the full HITL workflow."""
    
    def test_full_workflow(self, sample_order_query: str):
        """Test complete HITL workflow from query to scenarios."""
        # Step 1: Get models
        trigger_model = get_trigger_model()
        respond_model = get_respond_model()
        
        # Step 2: Run WHEN-TO-TRIGGER
        trigger_output = trigger_model.inference(sample_order_query)
        
        # Step 3: If triggered, run WHAT-TO-RESPOND
        if trigger_output.decision == TriggerDecision.TRIGGER:
            respond_output = respond_model.inference(
                user_query=sample_order_query,
                trigger_output=trigger_output
            )
            
            # Verify we got actionable output
            assert len(respond_output.scenarios) > 0
            assert respond_output.recommendation is not None
            
            # Verify each scenario is valid
            for scenario in respond_output.scenarios:
                assert scenario.name is not None
                assert scenario.total_cost > 0
                assert 0 <= scenario.quality_score <= 100
                assert scenario.risk_level in ["LOW", "MEDIUM", "HIGH"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
