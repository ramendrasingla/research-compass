import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, CheckCircle, XCircle, Download, ArrowLeft, Clock } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { apiClient } from '../utils/api'
import type { SessionDetail, WebSocketMessage } from '../types'

interface ResearchStep {
  id: string
  label: string
  status: 'pending' | 'active' | 'completed' | 'error'
}

export default function ResearchPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [steps, setSteps] = useState<ResearchStep[]>([
    { id: 'init', label: 'Initializing research agent', status: 'pending' },
    { id: 'brief', label: 'Writing research brief', status: 'pending' },
    { id: 'research', label: 'Conducting research', status: 'pending' },
    { id: 'report', label: 'Generating final report', status: 'pending' },
    { id: 'export', label: 'Preparing exports', status: 'pending' },
  ])
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!sessionId) return

    let isSubscribed = true
    let ws: WebSocket | null = null

    const initConnection = async () => {
      // Load session info first
      await loadSession()

      // Small delay to ensure session is fully created
      await new Promise(resolve => setTimeout(resolve, 100))

      // Only connect if component is still mounted
      if (isSubscribed) {
        console.log('🔌 Initializing WebSocket connection...')
        ws = connectWebSocket()
      }
    }

    initConnection()

    return () => {
      isSubscribed = false
      if (ws || wsRef.current) {
        console.log('🔌 Cleaning up WebSocket connection')
        const socket = ws || wsRef.current
        if (socket && socket.readyState !== WebSocket.CLOSED) {
          socket.close()
        }
        wsRef.current = null
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

  const updateStepFromEvent = (eventStr: string) => {
    // Parse the event string to determine which step is active
    if (eventStr.includes("'clarify_with_user'") || eventStr.includes('initialization')) {
      updateStep('init', 'completed')
    } else if (eventStr.includes("'write_research_brief'")) {
      updateStep('init', 'completed')
      updateStep('brief', 'active')
    } else if (eventStr.includes("'research_supervisor'")) {
      updateStep('brief', 'completed')
      updateStep('research', 'active')
    } else if (eventStr.includes("'final_report_generation'")) {
      updateStep('research', 'completed')
      updateStep('report', 'active')
    } else if (eventStr.includes("'export_reports'")) {
      updateStep('report', 'completed')
      updateStep('export', 'active')
    }
  }

  const updateStep = (stepId: string, status: 'pending' | 'active' | 'completed' | 'error') => {
    setSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, status } : step
    ))
  }

  const connectWebSocket = (): WebSocket | null => {
    if (!sessionId) return null

    console.log('🔌 Creating WebSocket connection to:', sessionId)
    const ws = apiClient.connectToResearchStream(sessionId)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      console.log('✅ WebSocket connected successfully')
    }

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      console.log('📨 WebSocket message:', message.type, message)

      // Update steps based on progress messages
      if (message.type === 'progress' && message.stage === 'initialization') {
        updateStep('init', 'active')
      } else if (message.type === 'progress' && message.event) {
        updateStepFromEvent(message.event)
      }

      // Handle completion
      if (message.type === 'complete' && message.result) {
        // Mark all steps as completed
        setSteps(prev => prev.map(step => ({ ...step, status: 'completed' as const })))
        setIsComplete(true)

        setSession((prev) => prev ? {
          ...prev,
          status: 'completed',
          result: message.result,
        } : null)
      }

      // Handle errors
      if (message.type === 'error') {
        console.error('❌ Research error:', message.message)
        // Mark current active step as error
        setSteps(prev => prev.map(step =>
          step.status === 'active' ? { ...step, status: 'error' as const } : step
        ))
      }

      setMessages((prev) => [...prev, message])
    }

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
      setMessages((prev) => [...prev, {
        type: 'error',
        message: 'Connection error occurred',
      }])
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('🔌 WebSocket disconnected')
    }

    return ws
  }

  const getStatusIcon = () => {
    if (!session) return <Loader2 className="w-5 h-5 animate-spin text-primary-600" />

    if (isComplete) {
      return <CheckCircle className="w-5 h-5 text-green-600" />
    }

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

    if (isComplete) {
      return 'Research completed successfully'
    }

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

  const getStepIcon = (status: 'pending' | 'active' | 'completed' | 'error') => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'active':
        return <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-gray-400" />
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

            {(isComplete || session.status === 'completed') && session.result?.final_report && (
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

              {/* Step Indicators */}
              <div className="space-y-3 mb-6">
                {steps.map((step, index) => (
                  <div key={step.id} className="flex items-start space-x-3">
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-0.5">
                      {getStepIcon(step.status)}
                    </div>

                    {/* Label and connector */}
                    <div className="flex-1">
                      <div className={`text-sm font-medium ${
                        step.status === 'completed' ? 'text-green-600' :
                        step.status === 'active' ? 'text-primary-600' :
                        step.status === 'error' ? 'text-red-600' :
                        'text-gray-400'
                      }`}>
                        {step.label}
                      </div>

                      {/* Connector line */}
                      {index < steps.length - 1 && (
                        <div className={`w-0.5 h-4 ml-2.5 mt-1 ${
                          step.status === 'completed' ? 'bg-green-200' : 'bg-gray-200'
                        }`} />
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Recent Messages */}
              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Activity</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {messages.length === 0 && (
                    <div className="text-xs text-gray-500">
                      Waiting for updates...
                    </div>
                  )}

                  {messages.slice(-5).reverse().map((message, index) => {
                    // Only show important messages
                    if (message.type === 'progress' && message.event) {
                      return null // Skip detailed progress events
                    }

                    return (
                      <div
                        key={index}
                        className={`p-2 rounded text-xs ${
                          message.type === 'error'
                            ? 'bg-red-50 text-red-700'
                            : message.type === 'complete'
                            ? 'bg-green-50 text-green-700'
                            : 'bg-gray-50 text-gray-700'
                        }`}
                      >
                        {message.type === 'complete' && (
                          <div className="flex items-center space-x-1">
                            <CheckCircle className="w-3 h-3 flex-shrink-0" />
                            <span>Completed successfully!</span>
                          </div>
                        )}

                        {message.type === 'error' && (
                          <div className="flex items-center space-x-1">
                            <XCircle className="w-3 h-3 flex-shrink-0" />
                            <span>{message.message}</span>
                          </div>
                        )}

                        {(message.type === 'status' || (message.type === 'progress' && !message.event)) && (
                          <span>{message.message}</span>
                        )}
                      </div>
                    )
                  })}

                  <div ref={messagesEndRef} />
                </div>
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
