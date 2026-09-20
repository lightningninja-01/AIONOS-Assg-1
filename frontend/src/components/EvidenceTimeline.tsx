import React, { useState } from 'react'
import type { Evidence } from '../api/client'

const SOURCE_ICONS: Record<string, string> = {
  meeting: '🗣',
  email: '📧',
  voice_note: '🎙',
  calendar: '📅',
}

const SOURCE_COLORS: Record<string, string> = {
  meeting: 'bg-purple-900 border-purple-600',
  email: 'bg-blue-900 border-blue-600',
  voice_note: 'bg-amber-900 border-amber-600',
  calendar: 'bg-green-900 border-green-600',
}

export function EvidenceTimeline({ evidence }: { evidence: Evidence[] }) {
  return (
    <div className="mt-3 space-y-2">
      {evidence.map((ev, i) => (
        <div
          key={ev.evidence_id}
          className={`rounded-lg border p-3 text-xs ${
            SOURCE_COLORS[ev.source.source_type] || 'bg-gray-800 border-gray-600'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-base">{SOURCE_ICONS[ev.source.source_type] || '📄'}</span>
            <span className="font-semibold text-gray-200">{ev.source.label}</span>
            {ev.updates_deadline && (
              <span className="ml-auto bg-orange-700 text-orange-100 text-[10px] px-1.5 py-0.5 rounded font-bold">↻ DEADLINE UPDATED</span>
            )}
            {ev.implies_completion && (
              <span className="ml-auto bg-green-700 text-green-100 text-[10px] px-1.5 py-0.5 rounded font-bold">✓ COMPLETED</span>
            )}
          </div>
          {ev.speaker && (
            <div className="text-gray-400 mb-1">Speaker: <span className="text-gray-200">{ev.speaker}</span></div>
          )}
          <blockquote className="border-l-2 border-gray-400 pl-2 text-gray-300 italic mb-1">
            &ldquo;{ev.excerpt}&rdquo;
          </blockquote>
          <div className="text-gray-400">→ <span className="text-gray-200">{ev.extracted_fact}</span></div>
        </div>
      ))}
    </div>
  )
}
