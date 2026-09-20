import React from 'react'
import type { ReasoningStep } from '../api/client'

const STATUS_ICON: Record<string, string> = {
  success: '✅',
  pending: '⏳',
  error: '❌',
}

export function AgentTrace({ steps, isLoading }: { steps: ReasoningStep[]; isLoading: boolean }) {
  if (!isLoading && steps.length === 0) return null

  const displaySteps = isLoading && steps.length === 0
    ? [{ step: 1, label: 'Processing...', detail: 'Contacting agent', status: 'pending' as const }]
    : steps

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 p-3 mt-2">
      <p className="text-xs text-gray-500 mb-2 font-mono">AGENT TRACE</p>
      <div className="space-y-2">
        {displaySteps.map((step) => (
          <div key={step.step} className="flex items-start gap-2">
            <span className="text-sm flex-shrink-0">{STATUS_ICON[step.status]}</span>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-gray-200">{step.label}</p>
              <p className="text-xs text-gray-400">{step.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
