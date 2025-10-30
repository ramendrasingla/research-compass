import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, CheckCircle, XCircle, Download, ArrowLeft } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { apiClient } from '../utils/api'
import type { SessionDetail, WebSocketMessage } from '../types'

export default function ResearchPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!sessionId) return

    // Load session info
    loadSession()

    // Connect to WebSocket
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [sessionId])

  useEffect(() => {
    // Auto-scroll to bottom of messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadSession = async () => {
    if (!sessionId) return
    try {
      const data = await apiClient.getSession(sessionId)
      setSession(data)
    } catch (error) {
      console.error('Failed to load session:', error)
    }
  }

  const connectWebSocket = () => {
    if (!sessionId) return

    const ws = apiClient.connectToResearchStream(sessionId)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      setMessages((prev) => [...prev, message])

      // Update session if complete
      if (message.type === 'complete' && message.result) {
        setSession((prev) => prev ? {
          ...prev,
          status: 'completed',
          result: message.result,
        } : null)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setMessages((prev) => [...prev, {
        type: 'error',
        message: 'Connection error occurred',
      }])
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')
    }
  }

  const getStatusIcon = () => {
    if (!session) return <Loader2 className="w-5 h-5 animate-spin text-primary-600" />

    switch (session.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
    }
  }

  const getStatusText = () => {
    if (!session) return 'Loading...'

    switch (session.status) {
      case 'initializing':
        return 'Initializing research...'
      case 'running':
        return 'Research in progress...'
      case 'completed':
        return 'Research completed'
      case 'error':
        return 'Research failed'
      case 'disconnected':
        return 'Connection lost'
      default:
        return 'Unknown status'
    }
  }

  const downloadReport = (format: string) => {
    if (!session?.result?.final_report) return

    const blob = new Blob([session.result.final_report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `research-report-${sessionId}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Home</span>
          </button>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {session.query}
              </h1>
              <div className="flex items-center space-x-2">
                {getStatusIcon()}
                <span className="text-sm font-medium text-gray-600">
                  {getStatusText()}
                </span>
                {isConnected && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Connected
                  </span>
                )}
              </div>
            </div>

            {session.status === 'completed' && session.result?.final_report && (
              <button
                onClick={() => downloadReport('markdown')}
                className="btn-secondary flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download Report</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Progress Panel */}
          <div className="lg:col-span-1">
            <div className="card sticky top-32">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Research Progress
              </h2>

              <div className="space-y-3">
                {messages.length === 0 && (
                  <div className="text-sm text-gray-500">
                    Waiting for updates...
                  </div>
                )}

                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg text-sm ${
                      message.type === 'error'
                        ? 'bg-red-50 text-red-800'
                        : message.type === 'complete'
                        ? 'bg-green-50 text-green-800'
                        : 'bg-blue-50 text-blue-800'
                    }`}
                  >
                    {message.type === 'status' && (
                      <div className="flex items-start space-x-2">
                        <Loader2 className="w-4 h-4 animate-spin mt-0.5 flex-shrink-0" />
                        <span>{message.message}</span>
                      </div>
                    )}

                    {message.type === 'progress' && (
                      <div>
                        <div className="font-medium mb-1">
                          {message.stage?.replace('_', ' ').toUpperCase()}
                        </div>
                        <div className="text-xs opacity-75">{message.message}</div>
                      </div>
                    )}

                    {message.type === 'complete' && (
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span>Research completed successfully!</span>
                      </div>
                    )}

                    {message.type === 'error' && (
                      <div className="flex items-start space-x-2">
                        <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        <span>{message.message}</span>
                      </div>
                    )}
                  </div>
                ))}

                <div ref={messagesEndRef} />
              </div>

              {/* Configuration Info */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  Configuration
                </h3>
                <dl className="space-y-2 text-xs">
                  <div>
                    <dt className="text-gray-600">Search API</dt>
                    <dd className="font-medium text-gray-900">
                      {session.config.search_api}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-600">Research Model</dt>
                    <dd className="font-medium text-gray-900">
                      {session.config.research_model.replace('openai:', '')}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-600">Max Iterations</dt>
                    <dd className="font-medium text-gray-900">
                      {session.config.max_researcher_iterations}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>

          {/* Report Panel */}
          <div className="lg:col-span-2">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Research Report
              </h2>

              {!session.result?.final_report ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Loader2 className="w-12 h-12 animate-spin text-primary-600 mb-4" />
                  <p className="text-gray-600">
                    Generating research report...
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    This may take a few minutes depending on the complexity of your query
                  </p>
                </div>
              ) : (
                <div className="markdown-body prose max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {session.result.final_report}
                  </ReactMarkdown>
                </div>
              )}

              {/* Exported Files */}
              {session.result?.exported_files && session.result.exported_files.length > 0 && (
                <div className="mt-8 pt-8 border-t border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">
                    Exported Files
                  </h3>
                  <ul className="space-y-2">
                    {session.result.exported_files.map((file, index) => (
                      <li key={index} className="text-sm">
                        <a
                          href="#"
                          className="text-primary-600 hover:text-primary-700 flex items-center space-x-2"
                        >
                          <Download className="w-4 h-4" />
                          <span>{file}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
