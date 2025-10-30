import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Clock, Trash2, ExternalLink, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { apiClient } from '../utils/api'
import type { SessionInfo } from '../types'

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    setIsLoading(true)
    try {
      const data = await apiClient.listSessions()
      // Sort by created_at descending
      const sorted = data.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      setSessions(sorted)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this research session?')) return

    try {
      await apiClient.deleteSession(sessionId)
      setSessions(sessions.filter(s => s.session_id !== sessionId))
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('Failed to delete session')
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            Completed
          </span>
        )
      case 'error':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <XCircle className="w-3 h-3 mr-1" />
            Error
          </span>
        )
      case 'running':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Running
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {status}
          </span>
        )
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Research History
          </h1>
          <p className="text-gray-600">
            View and manage your past research sessions
          </p>
        </div>

        {/* Sessions List */}
        {sessions.length === 0 ? (
          <div className="card text-center py-16">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No research sessions yet
            </h2>
            <p className="text-gray-600 mb-6">
              Start your first research to see it appear here
            </p>
            <Link to="/" className="btn-primary inline-block">
              Start Research
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div key={session.session_id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      {getStatusBadge(session.status)}
                      <span className="text-sm text-gray-500">
                        {format(new Date(session.created_at), 'MMM d, yyyy h:mm a')}
                      </span>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate">
                      {session.query}
                    </h3>

                    <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Search API:</span>{' '}
                        {session.config.search_api}
                      </div>
                      <div>
                        <span className="font-medium">Model:</span>{' '}
                        {session.config.research_model.replace('openai:', '')}
                      </div>
                      {session.config.export_formats.length > 0 && (
                        <div>
                          <span className="font-medium">Exports:</span>{' '}
                          {session.config.export_formats.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <Link
                      to={`/research/${session.session_id}`}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="View session"
                    >
                      <ExternalLink className="w-5 h-5" />
                    </Link>

                    <button
                      onClick={() => handleDelete(session.session_id)}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete session"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
