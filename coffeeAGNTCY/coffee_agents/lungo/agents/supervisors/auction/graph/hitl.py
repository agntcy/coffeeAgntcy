# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Human-in-the-Loop (HITL) Module for Coffee Exchange

This module implements a two-model approach for intelligent human intervention:

1. WHEN-TO-TRIGGER MODEL (Small Language Model)
   - Input: User query + context (budget, market data, etc.)
   - Output: Confidence score (0-1) and decision (TRIGGER or NO_TRIGGER)
   - Purpose: Decides if human intervention is needed
   
2. WHAT-TO-RESPOND MODEL (Small Language Model)
   - Input: User query + trigger context + inventory data
   - Output: Structured scenarios and recommendations
   - Purpose: Generates options for human review

This module provides:
- Abstract base classes for model inference
- Mock implementations for development/testing
- Ready-to-use inference hooks for real models

Reference: https://docs.langchain.com/oss/python/langgraph/interrupts
"""

import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger("lungo.supervisor.hitl")


# =============================================================================
# DATA MODELS
# =============================================================================

class TriggerDecision(str, Enum):
    """Decision from the WHEN-TO-TRIGGER model"""
    TRIGGER = "TRIGGER"
    NO_TRIGGER = "NO_TRIGGER"


@dataclass
class TriggerModelInput:
    """
    Input to the WHEN-TO-TRIGGER model.
    
    The model takes the raw user query directly - no preprocessing needed.
    The small language model is smart enough to understand the query.
    """
    user_query: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_query": self.user_query,
        }


@dataclass
class TriggerModelOutput:
    """
    Output from the WHEN-TO-TRIGGER model.
    
    This is what the model returns after inference.
    """
    decision: TriggerDecision
    confidence: float  # 0.0 to 1.0
    reasons: List[str]
    raw_output: Optional[str] = None  # Raw model output for debugging
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "raw_output": self.raw_output,
        }


@dataclass 
class AllocationScenario:
    """A single allocation scenario from WHAT-TO-RESPOND model"""
    name: str
    description: str
    farm_allocations: Dict[str, float]  # farm -> quantity in lbs
    total_cost: float
    quality_score: float  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "farm_allocations": self.farm_allocations,
            "total_cost": self.total_cost,
            "quality_score": self.quality_score,
            "risk_level": self.risk_level,
        }


@dataclass
class RespondModelInput:
    """
    Input to the WHAT-TO-RESPOND model.
    
    This is what gets passed to the model for inference.
    """
    user_query: str
    trigger_output: TriggerModelOutput
    inventory_data: Dict[str, Any] = field(default_factory=dict)
    historical_data: Dict[str, Any] = field(default_factory=dict)
    market_prices: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_query": self.user_query,
            "trigger_output": self.trigger_output.to_dict(),
            "inventory_data": self.inventory_data,
            "historical_data": self.historical_data,
            "market_prices": self.market_prices,
        }


@dataclass
class RespondModelOutput:
    """
    Output from the WHAT-TO-RESPOND model.
    
    This is what the model returns after inference.
    """
    summary: str
    scenarios: List[AllocationScenario]
    recommendation: str
    rationale: str
    additional_context: Dict[str, Any] = field(default_factory=dict)
    raw_output: Optional[str] = None  # Raw model output for debugging
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "additional_context": self.additional_context,
            "raw_output": self.raw_output,
        }


# =============================================================================
# ABSTRACT MODEL INTERFACES
# =============================================================================

class WhenToTriggerModelBase(ABC):
    """
    Abstract base class for WHEN-TO-TRIGGER model inference.
    
    The model takes the raw user query and decides if human intervention is needed.
    No preprocessing required - the model understands the query directly.
    
    Implement this interface to connect to the real model.
    """
    
    @abstractmethod
    def inference(self, user_query: str) -> TriggerModelOutput:
        """
        Run inference on the model.
        
        Args:
            user_query: The raw user query string
        
        Returns:
            TriggerModelOutput with decision, confidence, and reasons
        
        For mock implementation, returns simulated output.
        For real implementation, calls the model API/endpoint.
        """
        pass
    
    def analyze(self, user_query: str) -> TriggerModelOutput:
        """
        Main entry point for using the model.
        
        Simply calls inference with the user query.
        """
        return self.inference(user_query)


class WhatToRespondModelBase(ABC):
    """
    Abstract base class for WHAT-TO-RESPOND model inference.
    
    The model takes the user query and trigger output to generate options.
    
    Implement this interface to connect to the real model.
    """
    
    @abstractmethod
    def inference(
        self, 
        user_query: str, 
        trigger_output: TriggerModelOutput,
        inventory_data: Dict[str, Any] = None
    ) -> RespondModelOutput:
        """
        Run inference on the model.
        
        Args:
            user_query: The raw user query string
            trigger_output: Output from WHEN-TO-TRIGGER model
            inventory_data: Available inventory from farms (optional)
        
        Returns:
            RespondModelOutput with scenarios, recommendation, etc.
        
        For mock implementation, returns simulated output.
        For real implementation, calls the model API/endpoint.
        """
        pass
    
    def generate_options(
        self, 
        user_query: str, 
        trigger_output: TriggerModelOutput,
        inventory_data: Dict[str, Any] = None
    ) -> RespondModelOutput:
        """
        Main entry point for using the model.
        
        Simply calls inference with the inputs.
        """
        return self.inference(user_query, trigger_output, inventory_data)


# =============================================================================
# MOCK IMPLEMENTATIONS (Replace with real model inference later)
# =============================================================================

class MockWhenToTriggerModel(WhenToTriggerModelBase):
    """
    Mock implementation of WHEN-TO-TRIGGER model.
    
    Simulates model inference using rule-based logic.
    Replace with real model inference when available.
    
    INPUT: Raw user query string
        "I need to place our Q2 order. 500 lbs total, budget capped at $2,000"
    
    OUTPUT:
    {
        "decision": "TRIGGER",
        "confidence": 0.91,
        "reasons": [
            "Budget constraint present",
            "No origin specified", 
            "Market volatility detected (Q2 order)",
            "Standard order would exceed budget by $250"
        ]
    }
    """
    
    def __init__(self):
        self.name = "mock-when-to-trigger-v1"
        self.threshold = 0.65  # Confidence threshold for triggering
        logger.info(f"Initialized {self.name} (MOCK - replace with real model)")
    
    def inference(self, user_query: str) -> TriggerModelOutput:
        """
        MOCK INFERENCE - Simulates model response.
        
        The real model will take the raw user_query and return the decision.
        
        TODO: Replace this with actual model inference:
        
        ```python
        # Example real implementation:
        response = requests.post(
            "http://your-model-endpoint/predict",
            json={"user_query": user_query}
        )
        result = response.json()
        return TriggerModelOutput(
            decision=TriggerDecision(result["decision"]),
            confidence=result["confidence"],
            reasons=result["reasons"],
            raw_output=json.dumps(result)
        )
        ```
        """
        import re
        
        logger.info(f"[MOCK WHEN-TO-TRIGGER] Running mock inference on: {user_query}")
        
        query_lower = user_query.lower()
        
        # === MOCK LOGIC (simulates what the real model would understand) ===
        reasons = []
        confidence = 0.0
        
        # Detect budget constraint
        budget_keywords = ["budget", "cap", "capped", "max", "maximum", "limit", "under", "less than"]
        if any(kw in query_lower for kw in budget_keywords):
            reasons.append("Budget constraint present")
            confidence += 0.25
        
        # Detect missing origin
        farm_keywords = ["brazil", "colombia", "vietnam"]
        if not any(farm in query_lower for farm in farm_keywords):
            reasons.append("No origin specified")
            confidence += 0.20
        
        # Detect market volatility signals
        if any(q in query_lower for q in ["q1", "q2", "q3", "q4", "quarterly", "bulk"]):
            reasons.append("Market volatility detected (quarterly/bulk order)")
            confidence += 0.20
        
        # Detect budget vs quantity mismatch
        budget_match = re.search(r'\$[\d,]+', query_lower)
        qty_match = re.search(r'(\d+)\s*(?:lb|lbs|pound)', query_lower)
        
        if budget_match and qty_match:
            budget = float(budget_match.group().replace('$', '').replace(',', ''))
            qty = float(qty_match.group(1))
            avg_price = 4.50  # Simulated average price
            estimated_cost = qty * avg_price
            
            if estimated_cost > budget:
                exceeded_by = estimated_cost - budget
                reasons.append(f"Standard order would exceed budget by ${exceeded_by:.2f}")
                confidence += 0.26
        
        confidence = min(confidence, 1.0)
        decision = TriggerDecision.TRIGGER if confidence >= self.threshold else TriggerDecision.NO_TRIGGER
        
        output = TriggerModelOutput(
            decision=decision,
            confidence=confidence,
            reasons=reasons,
            raw_output=f"MOCK: confidence={confidence:.2f}, decision={decision.value}",
        )
        
        logger.info(f"[MOCK WHEN-TO-TRIGGER] Output: {output.to_dict()}")
        return output


class MockWhatToRespondModel(WhatToRespondModelBase):
    """
    Mock implementation of WHAT-TO-RESPOND model.
    
    Simulates model inference by generating realistic scenarios.
    Replace with real model inference when available.
    
    INPUT:
    - user_query: "I need to place our Q2 order. 500 lbs total, budget capped at $2,000"
    - trigger_output: {"decision": "TRIGGER", "confidence": 0.91, "reasons": [...]}
    - inventory_data: {"brazil": 247500, "colombia": 4200, "vietnam": 15000}
    
    OUTPUT:
    {
        "summary": "Order Analysis for: 500 lbs, Budget: $2,000.00...",
        "scenarios": [
            {"name": "Budget-Optimized", "total_cost": 1825.00, ...},
            {"name": "Quality-First", "total_cost": 2010.00, ...},
            ...
        ],
        "recommendation": "Recommend 'Balanced Diversification'...",
        "rationale": "Based on your 500 lb order with a $2,000 budget cap..."
    }
    """
    
    def __init__(self):
        self.name = "mock-what-to-respond-v1"
        logger.info(f"Initialized {self.name} (MOCK - replace with real model)")
    
    def inference(
        self, 
        user_query: str, 
        trigger_output: TriggerModelOutput,
        inventory_data: Dict[str, Any] = None
    ) -> RespondModelOutput:
        """
        MOCK INFERENCE - Simulates model response.
        
        The real model will take the user_query and trigger_output,
        then generate scenarios and recommendations.
        
        TODO: Replace this with actual model inference:
        
        ```python
        # Example real implementation:
        response = requests.post(
            "http://your-model-endpoint/generate",
            json={
                "user_query": user_query,
                "trigger_output": trigger_output.to_dict(),
                "inventory_data": inventory_data,
            }
        )
        result = response.json()
        
        scenarios = [AllocationScenario(**s) for s in result["scenarios"]]
        
        return RespondModelOutput(
            summary=result["summary"],
            scenarios=scenarios,
            recommendation=result["recommendation"],
            rationale=result["rationale"],
            raw_output=json.dumps(result)
        )
        ```
        """
        import re
        
        logger.info(f"[MOCK WHAT-TO-RESPOND] Running mock inference on: {user_query}")
        
        # === MOCK: Extract parameters from user query ===
        query_lower = user_query.lower()
        
        # Extract quantity
        qty_match = re.search(r'(\d+)\s*(?:lb|lbs|pound)', query_lower)
        quantity = float(qty_match.group(1)) if qty_match else 500
        
        # Extract budget
        budget_match = re.search(r'\$[\d,]+', query_lower)
        budget = float(budget_match.group().replace('$', '').replace(',', '')) if budget_match else 2000
        
        # Mock market prices
        prices = {"brazil": 3.80, "colombia": 4.20, "vietnam": 3.50}
        
        # Mock inventory
        inventory = inventory_data or {"brazil": 247500, "colombia": 4200, "vietnam": 15000}
        
        # === MOCK: Generate scenarios ===
        scenarios = []
        
        # Scenario 1: Budget-Optimized
        vietnam_qty = min(quantity, inventory.get("vietnam", 15000))
        brazil_qty = max(0, quantity - vietnam_qty)
        cost1 = (vietnam_qty * prices["vietnam"]) + (brazil_qty * prices["brazil"])
        
        scenarios.append(AllocationScenario(
            name="Budget-Optimized",
            description="Maximize quantity within budget using lowest-cost sources",
            farm_allocations={"vietnam": vietnam_qty, "brazil": brazil_qty} if brazil_qty > 0 else {"vietnam": vietnam_qty},
            total_cost=cost1,
            quality_score=83,
            risk_level="MEDIUM",
        ))
        
        # Scenario 2: Quality-First
        colombia_qty = min(150, inventory.get("colombia", 4200))
        brazil_qty = quantity - colombia_qty
        cost2 = (colombia_qty * prices["colombia"]) + (brazil_qty * prices["brazil"])
        
        scenarios.append(AllocationScenario(
            name="Quality-First",
            description="Prioritize highest-rated sources for premium quality",
            farm_allocations={"colombia": colombia_qty, "brazil": brazil_qty},
            total_cost=cost2,
            quality_score=91,
            risk_level="LOW",
        ))
        
        # Scenario 3: Balanced Diversification
        brazil_qty = int(quantity * 0.50)
        colombia_qty = int(quantity * 0.30)
        vietnam_qty = quantity - brazil_qty - colombia_qty
        cost3 = (brazil_qty * prices["brazil"]) + (colombia_qty * prices["colombia"]) + (vietnam_qty * prices["vietnam"])
        
        scenarios.append(AllocationScenario(
            name="Balanced Diversification",
            description="Spread risk across multiple origins with quality focus",
            farm_allocations={"brazil": brazil_qty, "colombia": colombia_qty, "vietnam": vietnam_qty},
            total_cost=cost3,
            quality_score=87,
            risk_level="LOW",
        ))
        
        # Scenario 4: Budget-Strict
        avg_price = sum(prices.values()) / len(prices)
        max_qty = int(budget / avg_price)
        cost4 = max_qty * prices["brazil"]
        
        scenarios.append(AllocationScenario(
            name="Budget-Strict",
            description=f"Reduce quantity to {max_qty} lbs to stay within ${budget:,.0f} budget",
            farm_allocations={"brazil": max_qty},
            total_cost=cost4,
            quality_score=86,
            risk_level="LOW",
        ))
        
        # Find best recommendation
        valid = [s for s in scenarios if s.total_cost <= budget]
        if valid:
            recommended = max(valid, key=lambda s: s.quality_score)
            recommendation = f"Recommend '{recommended.name}' - {recommended.description}"
        else:
            recommended = scenarios[-1]
            recommendation = f"Budget constraint requires reducing quantity. Recommend '{recommended.name}'"
        
        # Build summary
        summary = f"""**Order Analysis for: {int(quantity)} lbs, Budget: ${budget:,.2f}**

📊 **Market Conditions:**
- Brazil: ${prices['brazil']:.2f}/lb | Colombia: ${prices['colombia']:.2f}/lb | Vietnam: ${prices['vietnam']:.2f}/lb

⚠️ **Issues Detected:**
{chr(10).join(f"- {r}" for r in trigger_output.reasons)}

📦 **Available Inventory:**
- Brazil: {inventory.get('brazil', 'N/A'):,} lbs | Colombia: {inventory.get('colombia', 'N/A'):,} lbs | Vietnam: {inventory.get('vietnam', 'N/A'):,} lbs"""

        rationale = f"""Based on your {int(quantity)} lb order with a ${budget:,.2f} budget cap:

1. **Historical Pattern**: Previous orders averaged 85% Brazil sourcing
2. **Quality Requirement**: Minimum 84+ cupping score maintained
3. **Cost Analysis**: At current market rates, some scenarios exceed budget
4. **Recommendation**: {recommendation}

Please select a scenario or provide alternative instructions."""

        output = RespondModelOutput(
            summary=summary,
            scenarios=scenarios,
            recommendation=recommendation,
            rationale=rationale,
            additional_context={"market_prices": prices},
            raw_output="MOCK: Generated 4 scenarios",
        )
        
        logger.info(f"[MOCK WHAT-TO-RESPOND] Generated {len(scenarios)} scenarios")
        return output


# =============================================================================
# MODEL FACTORY
# =============================================================================

class HITLModelFactory:
    """
    Factory for creating HITL model instances.
    
    Switch between mock and real implementations here.
    """
    
    # Set to True when real models are ready
    USE_REAL_MODELS = False
    
    @classmethod
    def get_trigger_model(cls) -> WhenToTriggerModelBase:
        """Get the WHEN-TO-TRIGGER model instance"""
        if cls.USE_REAL_MODELS:
            # TODO: Return real model implementation
            # return RealWhenToTriggerModel(endpoint="http://...")
            raise NotImplementedError("Real WHEN-TO-TRIGGER model not yet implemented")
        return MockWhenToTriggerModel()
    
    @classmethod
    def get_respond_model(cls) -> WhatToRespondModelBase:
        """Get the WHAT-TO-RESPOND model instance"""
        if cls.USE_REAL_MODELS:
            # TODO: Return real model implementation
            # return RealWhatToRespondModel(endpoint="http://...")
            raise NotImplementedError("Real WHAT-TO-RESPOND model not yet implemented")
        return MockWhatToRespondModel()


# =============================================================================
# CONVENIENCE FUNCTIONS (backward compatible)
# =============================================================================

_trigger_model: Optional[WhenToTriggerModelBase] = None
_respond_model: Optional[WhatToRespondModelBase] = None


def get_trigger_model() -> WhenToTriggerModelBase:
    """Get or create the WHEN-TO-TRIGGER model singleton"""
    global _trigger_model
    if _trigger_model is None:
        _trigger_model = HITLModelFactory.get_trigger_model()
    return _trigger_model


def get_respond_model() -> WhatToRespondModelBase:
    """Get or create the WHAT-TO-RESPOND model singleton"""
    global _respond_model
    if _respond_model is None:
        _respond_model = HITLModelFactory.get_respond_model()
    return _respond_model


# =============================================================================
# EXAMPLE: REAL MODEL IMPLEMENTATION TEMPLATE
# =============================================================================

"""
When youß have the real models ready, implement like this:

```python
import requests

class RealWhenToTriggerModel(WhenToTriggerModelBase):
    '''
    Real WHEN-TO-TRIGGER model using HTTP inference endpoint.
    
    The model takes the raw user query and returns:
    - decision: TRIGGER or NO_TRIGGER
    - confidence: 0.0 to 1.0
    - reasons: list of strings explaining the decision
    '''
    
    def __init__(self, endpoint: str, api_key: str = None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.name = "real-when-to-trigger-v1"
    
    def inference(self, user_query: str) -> TriggerModelOutput:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        # Send raw user query to the model
        response = requests.post(
            f"{self.endpoint}/predict",
            json={"user_query": user_query},
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        
        return TriggerModelOutput(
            decision=TriggerDecision(result["decision"]),
            confidence=result["confidence"],
            reasons=result["reasons"],
            raw_output=json.dumps(result),
        )


class RealWhatToRespondModel(WhatToRespondModelBase):
    '''
    Real WHAT-TO-RESPOND model using HTTP inference endpoint.
    
    The model takes user query + trigger output and generates:
    - scenarios: list of allocation options
    - recommendation: suggested option
    - rationale: explanation
    '''
    
    def __init__(self, endpoint: str, api_key: str = None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.name = "real-what-to-respond-v1"
    
    def inference(
        self, 
        user_query: str, 
        trigger_output: TriggerModelOutput,
        inventory_data: Dict[str, Any] = None
    ) -> RespondModelOutput:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        response = requests.post(
            f"{self.endpoint}/generate",
            json={
                "user_query": user_query,
                "trigger_output": trigger_output.to_dict(),
                "inventory_data": inventory_data or {},
            },
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        
        scenarios = [AllocationScenario(**s) for s in result["scenarios"]]
        
        return RespondModelOutput(
            summary=result["summary"],
            scenarios=scenarios,
            recommendation=result["recommendation"],
            rationale=result["rationale"],
            raw_output=json.dumps(result),
        )
```

Then update HITLModelFactory.USE_REAL_MODELS = True and implement the factory methods.
"""
