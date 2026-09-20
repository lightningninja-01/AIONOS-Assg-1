import axios from 'axios'

// @ts-ignore - Bypass TS not knowing about Vite's import.meta.env
const BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://127.0.0.1:8001'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

export interface Evidence {
  evidence_id: string
  date: string
  time?: string
  source: {
    source_id: string
    source_type: 'meeting' | 'email' | 'voice_note' | 'calendar'
    date: string
    label: string
  }
  speaker?: string
  excerpt: string
  extracted_fact: string
  updates_deadline: boolean
  implies_completion: boolean
}

export interface Commitment {
  commitment_id: string
  title: string
  description: string
  owner: string
  ownership_status: 'confirmed' | 'suggested' | 'unknown'
  owner_display: string
  recipient?: string
  category: 'my_action' | 'waiting_on_others' | 'ownership_unclear'
  deadline_original?: string
  deadline_original_label?: string
  deadline_latest?: string
  deadline_latest_label?: string
  status: 'outstanding' | 'overdue' | 'due_today' | 'completed' | 'unclear'
  evidence: Evidence[]
  source_ids: string[]
  confidence: 'high' | 'medium' | 'low'
  extraction_notes?: string
}

export interface DailyBrief {
  as_of_date: string
  executive: string
  my_actions: Commitment[]
  waiting_on_others: Commitment[]
  ownership_unclear: Commitment[]
}

export interface ReasoningStep {
  step: number
  label: string
  detail: string
  status: 'success' | 'pending' | 'error'
}

export interface AnswerResponse {
  answer: string
  commitments_cited: Commitment[]
  confidence: 'high' | 'medium' | 'low'
  reasoning_steps: ReasoningStep[]
}

export async function fetchBrief(asOfDate: string): Promise<DailyBrief> {
  const { data } = await api.get(`/api/brief?as_of_date=${asOfDate}`)
  return data
}

export async function postQuery(question: string, asOfDate: string): Promise<AnswerResponse> {
  const { data } = await api.post('/api/query', { question, as_of_date: asOfDate })
  return data
}
