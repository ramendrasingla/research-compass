export interface PaperSource {
  source_id: string
  paper_id?: string
  title: string
  authors: string[]
  abstract: string
  url: string
  pdf_url?: string
  published_date?: string
  citation_count?: number
  venue?: string
  search_api: string
  accessed_at: string
}

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
    sources?: PaperSource[]
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
    sources?: PaperSource[]
  }
}
