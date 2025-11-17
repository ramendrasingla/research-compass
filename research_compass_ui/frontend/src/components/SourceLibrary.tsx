import React from 'react'
import { PaperSource } from '../types'
import { PaperCard } from './PaperCard'
import { BookOpen, Search } from 'lucide-react'

interface SourceLibraryProps {
  sources: PaperSource[]
  isLoading?: boolean
}

export const SourceLibrary: React.FC<SourceLibraryProps> = ({ sources, isLoading = false }) => {
  const [searchTerm, setSearchTerm] = React.useState('')

  // Filter sources based on search term
  const filteredSources = React.useMemo(() => {
    if (!searchTerm.trim()) return sources

    const term = searchTerm.toLowerCase()
    return sources.filter(source =>
      source.title.toLowerCase().includes(term) ||
      source.authors.some(author => author.toLowerCase().includes(term)) ||
      source.abstract.toLowerCase().includes(term)
    )
  }, [sources, searchTerm])

  // Get counts by API
  const apiCounts = React.useMemo(() => {
    const counts: Record<string, number> = {}
    sources.forEach(source => {
      counts[source.search_api] = (counts[source.search_api] || 0) + 1
    })
    return counts
  }, [sources])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading sources...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex-shrink-0">
        <div className="flex items-center gap-2 mb-3">
          <BookOpen className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Research Sources</h2>
          <span className="ml-auto text-sm text-gray-500">
            {sources.length} {sources.length === 1 ? 'paper' : 'papers'}
          </span>
        </div>

        {/* API Breakdown */}
        {Object.keys(apiCounts).length > 0 && (
          <div className="flex gap-2 mb-3">
            {Object.entries(apiCounts).map(([api, count]) => (
              <span
                key={api}
                className={`text-xs px-2 py-1 rounded-full ${
                  api === 'arxiv'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-purple-100 text-purple-800'
                }`}
              >
                {api === 'arxiv' ? 'ArXiv' : 'Semantic Scholar'}: {count}
              </span>
            ))}
          </div>
        )}

        {/* Search Bar */}
        {sources.length > 0 && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search papers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto p-4">
        {sources.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No sources found</p>
            <p className="text-sm text-gray-400 mt-2">
              Sources will appear here as research progresses
            </p>
          </div>
        ) : filteredSources.length === 0 ? (
          <div className="text-center py-12">
            <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No papers match your search</p>
            <button
              onClick={() => setSearchTerm('')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 underline"
            >
              Clear search
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredSources.map((source) => (
              <PaperCard key={source.source_id} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
