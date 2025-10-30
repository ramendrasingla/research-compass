import axios from 'axios'
import type { ResearchConfig, SessionInfo, SessionDetail, SearchAPI, ExportFormat } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

export const apiClient = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/api/health')
    return response.data
  },

  // Research operations
  startResearch: async (config: ResearchConfig): Promise<SessionInfo> => {
    const response = await api.post('/api/research/start', config)
    return response.data
  },

  listSessions: async (): Promise<SessionInfo[]> => {
    const response = await api.get('/api/research/sessions')
    return response.data
  },

  getSession: async (sessionId: string): Promise<SessionDetail> => {
    const response = await api.get(`/api/research/session/${sessionId}`)
    return response.data
  },

  deleteSession: async (sessionId: string) => {
    const response = await api.delete(`/api/research/session/${sessionId}`)
    return response.data
  },

  // Configuration
  getAvailableModels: async (): Promise<string[]> => {
    const response = await api.get('/api/config/models')
    return response.data.models
  },

  getSearchAPIs: async (): Promise<SearchAPI[]> => {
    const response = await api.get('/api/config/search-apis')
    return response.data.search_apis
  },

  getExportFormats: async (): Promise<ExportFormat[]> => {
    const response = await api.get('/api/config/export-formats')
    return response.data.formats
  },

  // WebSocket connection
  connectToResearchStream: (sessionId: string): WebSocket => {
    const wsUrl = API_BASE_URL.replace('http', 'ws')
    return new WebSocket(`${wsUrl}/api/research/stream/${sessionId}`)
  },
}
