import React, { useState, useEffect, useCallback } from 'react'
import { fetchBrief } from '../api/client'
import type { DailyBrief } from '../api/client'
import { BriefPanel } from '../components/BriefPanel'
import { ChatPanel } from '../components/ChatPanel'
import { DateSimulator } from '../components/DateSimulator'

const DEFAULT_DATE = '2026-09-23'

const DAY_NAMES: Record<string, string> = {
  '2026-09-21': 'Monday, 21 Sep 2026',
  '2026-09-22': 'Tuesday, 22 Sep 2026',
  '2026-09-23': 'Wednesday, 23 Sep 2026',
  '2026-09-24': 'Thursday, 24 Sep 2026',
  '2026-09-25': 'Friday, 25 Sep 2026',
}

export function Agent() {
  const [selectedDate, setSelectedDate] = useState(DEFAULT_DATE)
  const [brief, setBrief] = useState<DailyBrief | null>(null)
  const [briefLoading, setBriefLoading] = useState(true)
  const [briefError, setBriefError] = useState<string | null>(null)

  const loadBrief = useCallback(async (date: string) => {
    setBriefLoading(true)
    setBriefError(null)
    try {
      const data = await fetchBrief(date)
      setBrief(data)
    } catch (err: any) {
      setBriefError(err?.message || 'Unknown error')
    } finally {
      setBriefLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBrief(selectedDate)
  }, [selectedDate, loadBrief])

  const handleDateChange = (date: string) => {
    setSelectedDate(date)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-xl font-bold text-white">
                🤖 Executive Productivity Agent
              </h1>
              <p className="text-sm text-gray-400 mt-0.5">
                Arjun Malhotra — VP Sales, Veridian Corp
              </p>
            </div>
            <DateSimulator selectedDate={selectedDate} onChange={handleDateChange} />
          </div>
          <div className="mt-2">
            <span className="text-xs text-gray-500">Simulated: </span>
            <span className="text-xs text-blue-400 font-semibold">{DAY_NAMES[selectedDate]}</span>
            <span className="text-xs text-gray-600 ml-3">Ujjwal Prakash Singh · 2301010234</span>
          </div>
        </div>
      </header>

      {/* Main two-panel layout */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
        {/* Left — Brief */}
        <section className="flex flex-col min-h-0">
          <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-4">
            Today&apos;s Brief
          </h2>
          <div className="flex-1 overflow-y-auto">
            <BriefPanel brief={brief} loading={briefLoading} error={briefError} />
          </div>
        </section>

        {/* Divider (desktop) */}
        <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gray-800" aria-hidden />

        {/* Right — Chat */}
        <section className="flex flex-col min-h-0" style={{ height: 'calc(100vh - 140px)' }}>
          <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-4">
            Ask the Agent
          </h2>
          <div className="flex-1 min-h-0">
            <ChatPanel asOfDate={selectedDate} />
          </div>
        </section>
      </main>
    </div>
  )
}
