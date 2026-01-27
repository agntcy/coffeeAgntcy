# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import Mock
from src.agent_recruiter.models.recruiter_models import (
    RecruitmentCriteria, 
    RecruitmentExtractionResult,
    EvalScenarioExtraction,
    SearchStrategy,
    EvalScenario
)


class TestRecruitmentCriteriaFromPrompt:
    """Test suite for RecruitmentCriteria.from_prompt method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = self.mock_structured_llm

    def test_successful_full_extraction(self):
        """Test successful extraction with all fields populated."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="high",
            name="Python AI Developers",
            skills=["Python", "Machine Learning", "TensorFlow"],
            semantic_query="Python developers with AI experience",
            policies=["Remote work allowed", "Must have 3+ years experience"],
            evaluation_criteria=[
                EvalScenarioExtraction(
                    scenario="Code a simple ML model",
                    expected_outcome="Working model with good practices"
                )
            ],
            search_strategy=SearchStrategy.INTERSECTION
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Find Python developers with machine learning experience for our AI team"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is not None
        assert result.name == "Python AI Developers"
        assert result.skills == ["Python", "Machine Learning", "TensorFlow"]
        assert result.semantic_query == "Python developers with AI experience"
        assert result.policies == ["Remote work allowed", "Must have 3+ years experience"]
        assert len(result.evaluation_criteria) == 1
        assert result.evaluation_criteria[0].scenario == "Code a simple ML model"
        assert result.evaluation_criteria[0].expected_outcome == "Working model with good practices"
        assert result.search_strategy == SearchStrategy.INTERSECTION
        
        # Verify LLM was called correctly
        self.mock_llm.with_structured_output.assert_called_once_with(RecruitmentExtractionResult)
        self.mock_structured_llm.invoke.assert_called_once()

    def test_partial_extraction_skills_only(self):
        """Test partial extraction with only skills field populated."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="medium",
            name=None,
            skills=["databases", "SQL"],
            semantic_query=None,
            policies=[],
            evaluation_criteria=[],
            search_strategy=SearchStrategy.INTERSECTION
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Need someone good with databases"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is not None
        assert result.name is None
        assert result.skills == ["databases", "SQL"]
        assert result.semantic_query is None
        assert result.policies == []
        assert result.evaluation_criteria == []
        assert result.search_strategy == SearchStrategy.INTERSECTION

    def test_minimal_extraction_semantic_query_only(self):
        """Test minimal extraction with only semantic query."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="low",
            name=None,
            skills=[],
            semantic_query="project help",
            policies=[],
            evaluation_criteria=[],
            search_strategy=SearchStrategy.INTERSECTION
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Looking for help with our project"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is not None
        assert result.name is None
        assert result.skills == []
        assert result.semantic_query == "project help"
        assert result.policies == []
        assert result.evaluation_criteria == []

    def test_unrelated_prompt_returns_none(self):
        """Test that completely unrelated prompts return None."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=False,
            extraction_confidence="high",
            unmatched_reason="Prompt is about weather, not recruitment",
            name=None,
            skills=[],
            semantic_query=None,
            policies=[],
            evaluation_criteria=[],
            search_strategy=SearchStrategy.INTERSECTION
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "What's the weather like today?"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is None

    def test_different_search_strategies(self):
        """Test extraction with different search strategies."""
        test_cases = [
            (SearchStrategy.UNION, "union"),
            (SearchStrategy.RANKED, "ranked"),
            (SearchStrategy.INTERSECTION, "intersection")
        ]
        
        for expected_strategy, strategy_name in test_cases:
            # Arrange
            mock_result = RecruitmentExtractionResult(
                is_recruitment_related=True,
                extraction_confidence="high",
                skills=["Python"],
                search_strategy=expected_strategy
            )
            self.mock_structured_llm.invoke.return_value = mock_result
            
            prompt = f"Find developers using {strategy_name} search"
            
            # Act
            result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
            
            # Assert
            assert result is not None
            assert result.search_strategy == expected_strategy

    def test_multiple_evaluation_criteria(self):
        """Test extraction with multiple evaluation scenarios."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="high",
            skills=["Python"],
            evaluation_criteria=[
                EvalScenarioExtraction(
                    scenario="Technical interview",
                    expected_outcome="Demonstrates coding proficiency"
                ),
                EvalScenarioExtraction(
                    scenario="System design question",
                    expected_outcome="Shows architectural thinking"
                )
            ]
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Find developers who can pass technical interviews and system design"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is not None
        assert len(result.evaluation_criteria) == 2
        assert isinstance(result.evaluation_criteria[0], EvalScenario)
        assert result.evaluation_criteria[0].scenario == "Technical interview"
        assert result.evaluation_criteria[1].scenario == "System design question"

    def test_llm_exception_handling(self):
        """Test handling of LLM exceptions."""
        # Arrange
        self.mock_structured_llm.invoke.side_effect = Exception("LLM API error")
        
        prompt = "Find Python developers"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is None

    def test_structured_output_creation(self):
        """Test that structured output is correctly configured."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="high",
            skills=["Python"]
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Find Python developers"
        
        # Act
        RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        self.mock_llm.with_structured_output.assert_called_once_with(RecruitmentExtractionResult)

    def test_prompt_content_passed_to_llm(self):
        """Test that the prompt is correctly passed to the LLM."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="high",
            skills=["Python"]
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Find experienced Python developers"
        
        # Act
        RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        call_args = self.mock_structured_llm.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["role"] == "user"
        assert prompt in call_args[0]["content"]

    @pytest.mark.parametrize("confidence_level", ["high", "medium", "low"])
    def test_different_confidence_levels(self, confidence_level):
        """Test extraction with different confidence levels."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence=confidence_level,
            skills=["Python"]
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Find developers"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is not None
        assert result.skills == ["Python"]

    def test_empty_lists_handled_correctly(self):
        """Test that empty lists are handled correctly."""
        # Arrange
        mock_result = RecruitmentExtractionResult(
            is_recruitment_related=True,
            extraction_confidence="medium",
            skills=[],  # Empty skills list
            policies=[],  # Empty policies list
            evaluation_criteria=[]  # Empty evaluation criteria
        )
        self.mock_structured_llm.invoke.return_value = mock_result
        
        prompt = "Find someone"
        
        # Act
        result = RecruitmentCriteria.from_prompt(prompt, self.mock_llm)
        
        # Assert
        assert result is not None
        assert result.skills == []
        assert result.policies == []
        assert result.evaluation_criteria == []