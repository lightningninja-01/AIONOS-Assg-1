import React, { useState } from 'react'
import type { Commitment } from '../api/client'
import { EvidenceTimeline } from './EvidenceTimeline'

const STATUS_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
  overdue: { label: 'OVERDUE', color: 'text-red-400', dot: 'bg-red-500' },
  due_today: { label: 'DUE TODAY', color: 'text-orange-400', dot: 'bg-orange-500' },
  outstanding: { label: 'OUTSTANDING', color: 'text-yellow-400', dot: 'bg-yellow-500' },
  completed: { label: 'COMPLETED', color: 'text-green-400', dot: 'bg-green-500' },
  unclear: { label: 'UNCLEAR', color: 'text-gray-400', dot: 'bg-gray-500' },
}

export function CommitmentCard({ commitment }: { commitment: Commitment }) {
  const [expanded, setExpanded] = useState(false)
  const sc = STATUS_CONFIG[commitment.status] || STATUS_CONFIG.unclear

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${sc.dot}`} />
              <h3 className="font-semibold text-gray-100 text-sm leading-tight">{commitment.title}</h3>
            </div>

            <div className="space-y-0.5 text-xs text-gray-400">
              <div>
                <span className="text-gray-500">Owner:</span>{' '}
                <span className={commitment.ownership_status === 'unknown' ? 'text-red-400 font-semibold' : 'text-gray-200'}>
                  {commitment.owner_display}
                </span>
              </div>
              {commitment.recipient && (
                <div>
                  <span className="text-gray-500">For:</span>{' '}
                  <span className="text-gray-200">{commitment.recipient}</span>
                </div>
              )}
              {commitment.deadline_latest_label && (
                <div>
                  <span className="text-gray-500">Deadline:</span>{' '}
                  <span className="text-gray-200">{commitment.deadline_latest_label}</span>
                  {commitment.deadline_original_label &&
                    commitment.deadline_original_label !== commitment.deadline_latest_label && (
                      <span className="text-gray-500 ml-1">
                        (was: {commitment.deadline_original_label})
                      </span>
                    )}
                </div>
              )}
            </div>
          </div>

          <span className={`text-[10px] font-bold flex-shrink-0 ${sc.color}`}>{sc.label}</span>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
        >
          {expanded ? '▲ Hide' : '▶ Show'} sources ({commitment.evidence.length})
        </button>
      </div>

      {expanded && (
        <div className="border-t border-gray-700 p-4 bg-gray-850">
          <p className="text-xs text-gray-400 mb-2">Source evidence ({commitment.evidence.length} items):</p>
          <EvidenceTimeline evidence={commitment.evidence} />
        </div>
      )}
    </div>
  )
}
