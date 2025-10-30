export interface ResearchConfig {
  query: string
  search_api: string
  research_model: string
  summarization_model: string
  max_researcher_iterations: number
  max_concurrent_research_units: number
  export_formats: string[]
  allow_clarification: boolean
}

export interface SessionInfo {
  session_id: string
  query: string
  status: 'initializing' | 'running' | 'completed' | 'error' | 'disconnected'
  created_at: string
  updated_at: string
  config: ResearchConfig
}

export interface SessionDetail extends SessionInfo {
  result?: {
    final_report?: string
    exported_files?: string[]
  }
}

export interface SearchAPI {
  id: string
  name: string
  description: string
}

export interface ExportFormat {
  id: string
  name: string
  extension: string
}

export interface WebSocketMessage {
  type: 'status' | 'progress' | 'complete' | 'error'
  status?: string
  stage?: string
  event?: string
  message?: string
  result?: {
    final_report?: string
    exported_files?: string[]
  }
}
