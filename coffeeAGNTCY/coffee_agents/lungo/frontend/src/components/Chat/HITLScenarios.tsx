/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Human-in-the-Loop Scenarios Component
 *
 * Displays the two HITL models and their outputs:
 * 1. When-to-Trigger Model - Why human review was triggered
 * 2. How-to-Respond Model - Options for human selection
 */

import React from "react"
import { HITLInterrupt, HITLScenario } from "@/hooks/useHITLAPI"

interface HITLScenariosProps {
  interrupt: HITLInterrupt
  onSelect: (scenarioName: string) => void
  loading?: boolean
}

const ScenarioCard: React.FC<{
  scenario: HITLScenario
  isRecommended: boolean
  onSelect: () => void
  disabled?: boolean
}> = ({ scenario, isRecommended, onSelect, disabled }) => {
  const getRiskColor = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case "LOW":
        return "text-green-400"
      case "MEDIUM":
        return "text-yellow-400"
      case "HIGH":
        return "text-red-400"
      default:
        return "text-gray-400"
    }
  }

  return (
    <button
      onClick={onSelect}
      disabled={disabled}
      className={`
        w-full rounded-lg border p-4 text-left transition-all
        ${
          isRecommended
            ? "border-purple-500 bg-purple-500/10 hover:bg-purple-500/20"
            : "border-gray-600 bg-gray-800/50 hover:bg-gray-700/50"
        }
        ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"}
      `}
    >
      <div className="mb-2 flex items-center justify-between">
        <h4 className="font-semibold text-white">
          {scenario.name}
          {isRecommended && (
            <span className="ml-2 rounded bg-purple-500 px-2 py-0.5 text-xs text-white">
              Recommended
            </span>
          )}
        </h4>
        <span className={`text-sm font-medium ${getRiskColor(scenario.risk_level)}`}>
          {scenario.risk_level} Risk
        </span>
      </div>

      <p className="mb-3 text-sm text-gray-300">{scenario.description}</p>

      <div className="mb-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-400">Total Cost: </span>
          <span className="font-medium text-white">
            ${scenario.total_cost?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div>
          <span className="text-gray-400">Quality: </span>
          <span className="font-medium text-white">{scenario.quality_score}/100</span>
        </div>
      </div>

      <div className="text-sm">
        <span className="text-gray-400">Allocations: </span>
        <div className="mt-1 flex flex-wrap gap-2">
          {scenario.farm_allocations && Object.entries(scenario.farm_allocations).map(([farm, qty]) => (
            qty > 0 && (
              <span
                key={farm}
                className="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-200"
              >
                {farm.charAt(0).toUpperCase() + farm.slice(1)}: {qty} lbs
              </span>
            )
          ))}
        </div>
      </div>
    </button>
  )
}

const HITLScenarios: React.FC<HITLScenariosProps> = ({
  interrupt,
  onSelect,
  loading = false,
}) => {
  const triggerModel = interrupt.trigger_model
  const respondModel = interrupt.respond_model
  
  // Extract recommended scenario name from the recommendation string
  const getRecommendedName = (): string | null => {
    const recommendation = respondModel?.recommendation || interrupt.recommendation || ""
    const match = recommendation.match(/'([^']+)'/)
    return match ? match[1] : null
  }

  const recommendedName = getRecommendedName()
  const scenarios = respondModel?.scenarios || interrupt.scenarios || []

  return (
    <div className="w-full max-h-[60vh] overflow-y-auto rounded-lg border border-gray-600 bg-gray-900/80 p-4">
      {/* Header */}
      <div className="mb-4 border-b border-gray-700 pb-3">
        <h3 className="text-lg font-semibold text-white">Human Review Required</h3>
      </div>

      {/* Model 1: When-to-Trigger */}
      {triggerModel && (
        <div className="mb-4 rounded border border-blue-500/30 bg-blue-500/5 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div>
              <span className="text-xs font-medium uppercase tracking-wide text-blue-400">
                Model 1
              </span>
              <h4 className="font-semibold text-white">{triggerModel.name}</h4>
            </div>
            <div className="text-right">
              <span className="text-xs text-gray-400">Confidence</span>
              <div className="text-lg font-bold text-blue-400">
                {(triggerModel.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>
          <p className="mb-2 text-xs text-gray-400">{triggerModel.description}</p>
          <div className="text-sm">
            <span className="text-gray-300">Decision: </span>
            <span className="font-medium text-yellow-400">{triggerModel.decision}</span>
          </div>
          {triggerModel.reasons && triggerModel.reasons.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-gray-400">Reasons:</span>
              <ul className="mt-1 list-inside list-disc text-sm text-gray-300">
                {triggerModel.reasons.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Model 2: How-to-Respond */}
      {respondModel && (
        <div className="mb-4 rounded border border-green-500/30 bg-green-500/5 p-3">
          <div className="mb-2">
            <span className="text-xs font-medium uppercase tracking-wide text-green-400">
              Model 2
            </span>
            <h4 className="font-semibold text-white">{respondModel.name}</h4>
            <p className="text-xs text-gray-400">{respondModel.description}</p>
          </div>
          
          {/* Summary */}
          {respondModel.summary && (
            <div className="mt-2 rounded bg-gray-800/50 p-2 text-sm text-gray-200">
              <div
                dangerouslySetInnerHTML={{
                  __html: respondModel.summary
                    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
          )}
          
          {/* Rationale */}
          {respondModel.rationale && (
            <div className="mt-2 text-sm text-gray-300">
              <div
                dangerouslySetInnerHTML={{
                  __html: respondModel.rationale
                    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* Divider */}
      <div className="my-4 border-t border-gray-700" />

      {/* Selection Section */}
      <div className="mb-3">
        <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
          Select an Option
        </h4>
        <p className="text-xs text-gray-500">{interrupt.instructions}</p>
      </div>

      {/* Scenarios */}
      <div className="flex flex-col gap-3">
        {scenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.name}
            scenario={scenario}
            isRecommended={scenario.name === recommendedName}
            onSelect={() => onSelect(scenario.name)}
            disabled={loading}
          />
        ))}
      </div>

      {loading && (
        <div className="mt-4 text-center text-sm text-purple-400">
          Processing your selection...
        </div>
      )}
    </div>
  )
}

export default HITLScenarios
