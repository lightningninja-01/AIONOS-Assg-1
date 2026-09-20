import React from 'react'
import type { DailyBrief } from '../api/client'
import { CommitmentCard } from './CommitmentCard'

function Section({
  icon,
  title,
  color,
  items,
  emptyText,
}: {
  icon: string
  title: string
  color: string
  items: any[]
  emptyText: string
}) {
  return (
    <div className="mb-6">
      <div className={`flex items-center gap-2 mb-3 text-sm font-bold ${color}`}>
        <span>{icon}</span>
        <span>{title}</span>
        <span className="bg-gray-700 text-gray-300 text-xs px-2 py-0.5 rounded-full font-normal">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-gray-500 italic pl-6">{emptyText}</p>
      ) : (
        <div className="space-y-3">
          {items.map((c) => <CommitmentCard key={c.commitment_id} commitment={c} />)}
        </div>
      )}
    </div>
  )
}

export function BriefPanel({
  brief,
  loading,
  error,
}: {
  brief: DailyBrief | null
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 text-sm animate-pulse">Loading brief...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
        <p className="text-red-400 text-sm">Failed to load brief: {error}</p>
        <p className="text-red-500 text-xs mt-1">Ensure the backend is running at localhost:8001</p>
      </div>
    )
  }

  if (!brief) return null

  return (
    <div>
      <Section
        icon="🔴"
        title="My Actions"
        color="text-red-400"
        items={brief.my_actions}
        emptyText="No pending actions"
      />
      <Section
        icon="🟡"
        title="Waiting on Others"
        color="text-yellow-400"
        items={brief.waiting_on_others}
        emptyText="No items waiting on others"
      />
      <Section
        icon="⚠️"
        title="Ownership Unclear"
        color="text-orange-400"
        items={brief.ownership_unclear}
        emptyText="No unclear ownership items"
      />
    </div>
  )
}
