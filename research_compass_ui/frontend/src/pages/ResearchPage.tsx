import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Loader2, CheckCircle, XCircle, Download, ArrowLeft, Clock } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { apiClient } from '../utils/api'
import type { SessionDetail, WebSocketMessage } from '../types'
import ResearchTreeGraph from '../components/ResearchTreeGraph'
import ResearchDetailModal from '../components/ResearchDetailModal'
import { SourceLibrary } from '../components/SourceLibrary'

interface ResearchStep {
  id: string
  label: string
  status: 'pending' | 'active' | 'completed' | 'error'
}

interface ResearchTopicNode {
  id: string
  topic: string
  status: 'pending' | 'active' | 'completed' | 'error'
  iteration?: number
  startTime?: Date
  endTime?: Date
  findings?: string
  sources?: string[]
  searchApi?: string
}

export default function ResearchPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [steps, setSteps] = useState<ResearchStep[]>([
    { id: 'init', label: 'Getting ready', status: 'pending' },
    { id: 'brief', label: 'Understanding your question', status: 'pending' },
    { id: 'research', label: 'Researching topics', status: 'pending' },
    { id: 'report', label: 'Writing your report', status: 'pending' },
    { id: 'export', label: 'Finishing up', status: 'pending' },
  ])

  // Research tree visualization state
  const [supervisorStatus, setSupervisorStatus] = useState<'idle' | 'thinking' | 'delegating' | 'completed'>('idle')
  const [currentIteration, setCurrentIteration] = useState(0)
  const [researchTopics, setResearchTopics] = useState<ResearchTopicNode[]>([])
  const [selectedTopic, setSelectedTopic] = useState<ResearchTopicNode | null>(null)

  const wsRef = useRef<WebSocket | null>(null)

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
    } else if (eventStr.includes("'research_supervisor'") ||
               eventStr.includes("'researcher'") ||
               eventStr.includes("'compress_research'") ||
               eventStr.includes("'supervisor_tools'")) {
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

  const parseResearchEvent = (eventStr: string) => {
    // Parse event string to extract research topic information
    try {
      // Log full event periodically for debugging
      if (Math.random() < 0.1) { // Log 10% of events fully
        console.log('📊 Full event sample:', eventStr)
      }

      // Track research iterations FIRST so we have the correct value
      if (eventStr.includes('research_iterations')) {
        const iterMatch = /research_iterations['"]\s*[:=]\s*(\d+)/i.exec(eventStr)
        if (iterMatch) {
          const newIteration = parseInt(iterMatch[1], 10)
          console.log('🔢 Iteration:', newIteration)
          setCurrentIteration(newIteration)
        }
      }

      // Check if supervisor is active - multiple patterns
      if (eventStr.includes("supervisor") && !eventStr.includes("supervisor_tools")) {
        console.log('🧠 Supervisor thinking')
        setSupervisorStatus('thinking')
      }

      // Check if supervisor is delegating research - look for ConductResearch tool
      if (eventStr.includes("ConductResearch") || eventStr.includes("conduct_research")) {
        console.log('📤 Supervisor delegating research')
        setSupervisorStatus('delegating')

        // Extract the current iteration - try to find it in this specific event
        const iterMatch = /research_iterations['"]\s*[:=]\s*(\d+)/i.exec(eventStr)
        let currentIter = iterMatch ? parseInt(iterMatch[1], 10) : currentIteration

        // Update global iteration if found
        if (iterMatch && currentIter > currentIteration) {
          console.log('🔢 Updated iteration from event:', currentIter)
          setCurrentIteration(currentIter)
        }

        // Default to 1 if still not set
        if (!currentIter) currentIter = 1

        // Try multiple patterns for research topics
        const patterns = [
          /research_topic['"]\s*[:=]\s*['"]([^'"]+)['"]/gi,
          /ConductResearch\([^)]*['"]([^'"]{20,})['"]/gi,
          /'research_topic':\s*'([^']+)'/gi,
          /"research_topic":\s*"([^"]+)"/gi,
        ]

        let foundAny = false
        for (const pattern of patterns) {
          let match
          while ((match = pattern.exec(eventStr)) !== null) {
            const topic = match[1]
            if (topic && topic.length > 10) { // At least 10 chars for valid topic
              console.log('🔍 Found research topic:', topic, 'Iteration:', currentIter)
              foundAny = true
              const topicId = `topic-${Date.now()}-${Math.random()}`

              // Check if this topic already exists
              setResearchTopics(prev => {
                const exists = prev.some(t => t.topic === topic)
                if (!exists) {
                  console.log('✅ Adding new topic to state')
                  return [...prev, {
                    id: topicId,
                    topic: topic,
                    status: 'active',
                    iteration: currentIter,
                    startTime: new Date(),
                    sources: [],
                  }]
                }
                console.log('⚠️ Topic already exists, skipping')
                return prev
              })
            }
          }
        }

        if (!foundAny) {
          console.log('⚠️ ConductResearch found but no topic extracted. Event:', eventStr.substring(0, 300))
        }
      }

      // Extract search API and sources from researcher tool calls
      if (eventStr.includes("'researcher_tools'") || eventStr.includes('"researcher_tools"')) {
        // Try to extract search results and sources
        const searchPatterns = [
          /arxiv_search/i,
          /tavily_search/i,
          /exa_search/i,
          /you_search/i,
        ]

        let searchApi = ''
        for (const pattern of searchPatterns) {
          if (pattern.test(eventStr)) {
            searchApi = pattern.source.replace('_search', '').replace(/\\/gi, '').replace(/i$/, '')
            break
          }
        }

        // Extract source URLs or titles from search results
        const sources: string[] = []

        // Look for URLs in the event
        const urlPattern = /https?:\/\/[^\s'"]+/gi
        const urlMatches = eventStr.match(urlPattern)
        if (urlMatches) {
          sources.push(...urlMatches.slice(0, 3)) // Take first 3 URLs
        }

        // Look for paper titles or article titles
        const titlePattern = /title['"]\s*[:=]\s*['"]([^'"]{10,100})['"]/gi
        let titleMatch
        while ((titleMatch = titlePattern.exec(eventStr)) !== null && sources.length < 3) {
          sources.push(titleMatch[1])
        }

        // Update the most recent active topic with sources
        if ((searchApi || sources.length > 0)) {
          setResearchTopics(prev => {
            const activeTopics = prev.filter(t => t.status === 'active')
            if (activeTopics.length > 0) {
              const lastActive = activeTopics[activeTopics.length - 1]
              return prev.map(t =>
                t.id === lastActive.id
                  ? {
                      ...t,
                      searchApi: searchApi || t.searchApi,
                      sources: sources.length > 0 ? [...(t.sources || []), ...sources].slice(0, 5) : t.sources
                    }
                  : t
              )
            }
            return prev
          })
        }
      }

      // Check for compressed research (completed research)
      if (eventStr.includes('compressed_research') && eventStr.includes("'compress_research'")) {
        // Try to extract the research topic and findings
        const compressedMatch = /compressed_research['"]\s*[:=]\s*['"]([^'"]{0,500})/i.exec(eventStr)
        if (compressedMatch) {
          const findings = compressedMatch[1]

          // Mark the most recent active topic as completed with findings
          setResearchTopics(prev => {
            const activeTopics = prev.filter(t => t.status === 'active')
            if (activeTopics.length > 0) {
              const lastActive = activeTopics[activeTopics.length - 1]
              return prev.map(t =>
                t.id === lastActive.id
                  ? { ...t, status: 'completed', findings, endTime: new Date() }
                  : t
              )
            }
            return prev
          })
        }
      }

      // Check if research supervisor is complete
      if (eventStr.includes("'final_report_generation'")) {
        setSupervisorStatus('completed')
        // Mark any remaining active topics as completed
        setResearchTopics(prev => prev.map(t =>
          t.status === 'active' ? { ...t, status: 'completed', endTime: new Date() } : t
        ))
      }
    } catch (error) {
      console.error('Error parsing research event:', error)
    }
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
        // Parse the event for research tree visualization
        parseResearchEvent(message.event)
      }

      // Handle completion
      if (message.type === 'complete') {
        // Check if research failed
        if (message.status === 'failed' || message.error) {
          console.error('❌ Research failed:', message.error || message.message)
          // Mark all steps up to research as completed, but research as error
          setSteps(prev => prev.map(step => {
            if (step.id === 'research') return { ...step, status: 'error' as const }
            if (step.id === 'init' || step.id === 'brief') return { ...step, status: 'completed' as const }
            return { ...step, status: 'pending' as const }
          }))
          setSession((prev) => prev ? {
            ...prev,
            status: 'failed',
            result: { error: message.error || message.message || 'Research failed' },
          } : null)
          return
        }

        // Success case
        if (message.result) {
          // Mark all steps as completed
          setSteps(prev => prev.map(step => ({ ...step, status: 'completed' as const })))
          setIsComplete(true)

          setSession((prev) => prev ? {
            ...prev,
            status: 'completed',
            result: message.result,
          } : null)
        }
      }

      // Handle errors
      if (message.type === 'error') {
        console.error('❌ Research error:', message.message)
        // Mark current active step as error
        setSteps(prev => prev.map(step =>
          step.status === 'active' ? { ...step, status: 'error' as const } : step
        ))
      }
    }

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
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

  const downloadMarkdown = () => {
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

  const getExportFormatInfo = (filePath: string) => {
    const extension = filePath.split('.').pop()?.toLowerCase()
    const fileName = filePath.split('/').pop() || filePath

    const formatMap: Record<string, { label: string; icon: string }> = {
      'pdf': { label: 'PDF', icon: '📄' },
      'html': { label: 'HTML', icon: '🌐' },
      'docx': { label: 'Word', icon: '📝' },
      'md': { label: 'Markdown', icon: '📋' },
      'json': { label: 'JSON', icon: '📊' },
      'txt': { label: 'Text', icon: '📃' },
    }

    return {
      extension: extension || 'unknown',
      fileName,
      ...formatMap[extension || ''] || { label: extension?.toUpperCase() || 'File', icon: '📁' }
    }
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

            {(isComplete || session.status === 'completed') && (
              <div className="flex items-center gap-2">
                {/* Markdown download always available */}
                {session.result?.final_report && (
                  <button
                    onClick={downloadMarkdown}
                    className="btn-secondary flex items-center space-x-2"
                    title="Download as Markdown"
                  >
                    <Download className="w-4 h-4" />
                    <span>📋 Markdown</span>
                  </button>
                )}

                {/* Show other export formats if available */}
                {session.result?.exported_files && session.result.exported_files.length > 0 && (
                  session.result.exported_files
                    .filter(file => !file.endsWith('.md')) // Skip markdown as we handle it above
                    .slice(0, 2) // Show max 2 additional formats in header
                    .map((file, index) => {
                      const info = getExportFormatInfo(file)
                      return (
                        <button
                          key={index}
                          className="btn-secondary flex items-center space-x-2"
                          title={`Download ${info.label} file`}
                          onClick={() => {
                            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                            const downloadUrl = `${apiUrl}/api/research/download/${encodeURIComponent(file)}`
                            window.open(downloadUrl, '_blank')
                          }}
                        >
                          <Download className="w-4 h-4" />
                          <span>{info.icon} {info.label}</span>
                        </button>
                      )
                    })
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Progress Panel - Left Sidebar */}
          <div className="lg:w-80 flex-shrink-0">
            <div className="card sticky top-32">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Research Progress
              </h2>

              {/* Step Indicators */}
              <div className="space-y-3 mb-6">
                {steps.map((step, index) => (
                  <div key={step.id}>
                    <div className="flex items-start space-x-3">
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

                        {/* Research Tree for "Researching topics" step */}
                        {step.id === 'research' && (step.status === 'active' || step.status === 'completed') && (
                          <ResearchTreeGraph
                            supervisorStatus={supervisorStatus}
                            currentIteration={currentIteration}
                            maxIterations={session?.config.max_researcher_iterations || 6}
                            researchTopics={researchTopics}
                            compact={true}
                            onTopicClick={setSelectedTopic}
                          />
                        )}

                        {/* Connector line */}
                        {index < steps.length - 1 && (
                          <div className={`w-0.5 h-4 ml-2.5 mt-1 ${
                            step.status === 'completed' ? 'bg-green-200' : 'bg-gray-200'
                          }`} />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
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

          {/* Report Panel - Center */}
          <div className="flex-1 min-w-0">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Research Report
              </h2>

              {/* Error state - research failed */}
              {session.status === 'failed' || session.result?.error ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <XCircle className="w-16 h-16 text-red-500 mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Research Failed</h3>
                  <p className="text-gray-600 max-w-2xl mb-4">
                    {session.result?.error || 'All researchers failed to complete. This may be due to rate limits, network issues, or other errors.'}
                  </p>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-2xl text-left">
                    <p className="text-sm font-medium text-red-800 mb-2">Common solutions:</p>
                    <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                      <li>Switch to gpt-4o-mini model (faster, higher rate limits, cheaper)</li>
                      <li>Reduce max iterations or concurrent researchers</li>
                      <li>Wait a few minutes and try again if rate limited</li>
                      <li>Check your OpenAI API key has sufficient credits</li>
                    </ul>
                  </div>
                  <button
                    onClick={() => navigate('/')}
                    className="mt-6 btn-primary"
                  >
                    Start New Research
                  </button>
                </div>
              ) : !session.result?.final_report ? (
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
                    Exported Files ({session.result.exported_files.length})
                  </h3>
                  <p className="text-xs text-gray-600 mb-3">
                    These files have been saved on the server in the configured export directory.
                  </p>
                  <div className="space-y-2">
                    {session.result.exported_files.map((file, index) => {
                      const info = getExportFormatInfo(file)
                      return (
                        <div
                          key={index}
                          className="p-3 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 min-w-0 flex-1">
                              <span className="text-lg">{info.icon}</span>
                              <div className="min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {info.fileName}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {info.label} format
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <button
                                onClick={() => {
                                  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                                  const downloadUrl = `${apiUrl}/api/research/download/${encodeURIComponent(file)}`
                                  window.open(downloadUrl, '_blank')
                                }}
                                className="px-3 py-1 text-xs text-white bg-primary-600 hover:bg-primary-700 rounded transition-colors"
                              >
                                Download
                              </button>
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(file)
                                  alert(`Filename copied: ${file}`)
                                }}
                                className="text-xs text-gray-600 hover:text-gray-700"
                                title="Copy filename"
                              >
                                Copy
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Source Library - Right Sidebar */}
          <div className="lg:w-96 flex-shrink-0">
            <div className="sticky top-32 h-[calc(100vh-10rem)]">
              <div className="h-full bg-white rounded-lg shadow overflow-hidden">
                <SourceLibrary
                  sources={session.result?.sources || []}
                  isLoading={!isComplete && session.status !== 'completed'}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Research Detail Modal */}
      <ResearchDetailModal
        topic={selectedTopic}
        onClose={() => setSelectedTopic(null)}
      />
    </div>
  )
}
