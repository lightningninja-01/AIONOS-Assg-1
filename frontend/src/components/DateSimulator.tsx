import React from 'react'

const DAYS = [
  { label: 'Mon', date: '2026-09-21', full: 'Monday 21 Sep' },
  { label: 'Tue', date: '2026-09-22', full: 'Tuesday 22 Sep' },
  { label: 'Wed', date: '2026-09-23', full: 'Wednesday 23 Sep' },
  { label: 'Thu', date: '2026-09-24', full: 'Thursday 24 Sep' },
  { label: 'Fri', date: '2026-09-25', full: 'Friday 25 Sep' },
]

export function DateSimulator({
  selectedDate,
  onChange,
}: {
  selectedDate: string
  onChange: (date: string) => void
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 mr-1">Simulated date:</span>
      {DAYS.map((day) => (
        <button
          key={day.date}
          onClick={() => onChange(day.date)}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
            selectedDate === day.date
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
          }`}
          title={day.full}
        >
          {day.label}
        </button>
      ))}
    </div>
  )
}
