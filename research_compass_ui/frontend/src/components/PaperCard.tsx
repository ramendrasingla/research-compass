import React from 'react'
import { PaperSource } from '../types'
import { ExternalLink, FileText, File } from 'lucide-react'

interface PaperCardProps {
  source: PaperSource
}

export const PaperCard: React.FC<PaperCardProps> = ({ source }) => {
  const handleClick = () => {
    window.open(source.url, '_blank', 'noopener,noreferrer')
  }

  // Format authors (show first 2, then "et al." if more)
  const formatAuthors = (authors: string[]) => {
    if (authors.length === 0) return 'Unknown authors'
    if (authors.length <= 2) return authors.join(', ')
    return `${authors.slice(0, 2).join(', ')} et al.`
  }

  // Get badge color based on search API
  const getBadgeColor = (api: string) => {
    switch (api) {
      case 'arxiv':
        return 'bg-blue-100 text-blue-800'
      case 'semantic_scholar':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Format API name
  const formatApiName = (api: string) => {
    if (api === 'arxiv') return 'ArXiv'
    if (api === 'semantic_scholar') return 'Semantic Scholar'
    return api
  }

  return (
    <div
      onClick={handleClick}
      className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer bg-white"
    >
      <div className="flex gap-4">
        {/* PDF Icon/Preview */}
        <div className="flex-shrink-0">
          {source.pdf_url ? (
            <div className="w-16 h-20 bg-red-50 border-2 border-red-200 rounded flex flex-col items-center justify-center gap-1">
              <FileText className="w-8 h-8 text-red-600" />
              <span className="text-xs font-bold text-red-600">PDF</span>
            </div>
          ) : (
            <div className="w-16 h-20 bg-gray-50 border-2 border-gray-200 rounded flex flex-col items-center justify-center gap-1">
              <File className="w-8 h-8 text-gray-400" />
              <span className="text-xs font-semibold text-gray-500">Doc</span>
            </div>
          )}
        </div>

        {/* Paper Info */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-semibold text-gray-900 text-sm leading-tight mb-2 line-clamp-2 hover:text-blue-600">
            {source.title}
          </h3>

          {/* Authors */}
          <p className="text-xs text-gray-600 mb-2">
            {formatAuthors(source.authors)}
          </p>

          {/* Metadata */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Source Badge */}
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${getBadgeColor(source.search_api)}`}>
              {formatApiName(source.search_api)}
            </span>

            {/* Published Date */}
            {source.published_date && (
              <span className="text-xs text-gray-500">
                {source.published_date}
              </span>
            )}

            {/* Citation Count */}
            {source.citation_count !== undefined && source.citation_count !== null && (
              <span className="text-xs text-gray-500">
                {source.citation_count} citations
              </span>
            )}

            {/* Venue */}
            {source.venue && (
              <span className="text-xs text-gray-500 truncate max-w-[200px]">
                {source.venue}
              </span>
            )}
          </div>

          {/* External Link Icon */}
          <div className="mt-2">
            <ExternalLink className="w-3 h-3 text-gray-400 inline" />
            <span className="text-xs text-gray-400 ml-1">Click to open</span>
          </div>
        </div>
      </div>
    </div>
  )
}
