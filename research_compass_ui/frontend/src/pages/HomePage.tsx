import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Settings, ChevronDown, ChevronUp } from 'lucide-react'
import { apiClient } from '../utils/api'
import type { SearchAPI, ExportFormat } from '../types'

export default function HomePage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Configuration state
  const [searchAPIs, setSearchAPIs] = useState<SearchAPI[]>([])
  const [models, setModels] = useState<string[]>([])
  const [exportFormats, setExportFormats] = useState<ExportFormat[]>([])

  // Form state
  const [selectedSearchAPI, setSelectedSearchAPI] = useState('arxiv')
  const [selectedResearchModel, setSelectedResearchModel] = useState('openai:gpt-4o')
  const [selectedSummarizationModel, setSelectedSummarizationModel] = useState('openai:gpt-4o-mini')
  const [maxIterations, setMaxIterations] = useState(6)
  const [maxConcurrentUnits, setMaxConcurrentUnits] = useState(5)
  const [selectedExportFormats, setSelectedExportFormats] = useState<string[]>([])
  const [allowClarification, setAllowClarification] = useState(false)

  useEffect(() => {
    loadConfiguration()
  }, [])

  const loadConfiguration = async () => {
    try {
      const [apis, modelsList, formats] = await Promise.all([
        apiClient.getSearchAPIs(),
        apiClient.getAvailableModels(),
        apiClient.getExportFormats(),
      ])
      setSearchAPIs(apis)
      setModels(modelsList)
      setExportFormats(formats)
    } catch (error) {
      console.error('Failed to load configuration:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    console.log('🚀 Starting research with query:', query.trim())

    try {
      console.log('📤 Sending request to /api/research/start...')
      const session = await apiClient.startResearch({
        query: query.trim(),
        search_api: selectedSearchAPI,
        research_model: selectedResearchModel,
        summarization_model: selectedSummarizationModel,
        max_researcher_iterations: maxIterations,
        max_concurrent_research_units: maxConcurrentUnits,
        export_formats: selectedExportFormats,
        allow_clarification: allowClarification,
      })

      console.log('✅ Session created:', session)
      console.log('   Session ID:', session.session_id)
      console.log('   Status:', session.status)

      // Navigate to research page
      console.log('🔄 Navigating to /research/' + session.session_id)
      navigate(`/research/${session.session_id}`)
    } catch (error) {
      console.error('❌ Failed to start research:', error)
      if (error instanceof Error) {
        console.error('   Error message:', error.message)
        console.error('   Error stack:', error.stack)
      }
      alert(`Failed to start research: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleExportFormat = (formatId: string) => {
    setSelectedExportFormats(prev =>
      prev.includes(formatId)
        ? prev.filter(id => id !== formatId)
        : [...prev, formatId]
    )
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-4xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            AI-Powered Research Assistant
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Search academic papers, synthesize findings, and generate comprehensive research reports
            powered by advanced AI agents.
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSubmit} className="card">
          <div className="flex items-start space-x-4">
            <div className="flex-1">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your research question... (e.g., 'What are the latest advances in quantum computing?')"
                className="input resize-none"
                rows={4}
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Advanced Options */}
          <div className="mt-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <Settings className="w-4 h-4" />
              <span>Advanced Options</span>
              {showAdvanced ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {showAdvanced && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                {/* Search API */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search API
                  </label>
                  <select
                    value={selectedSearchAPI}
                    onChange={(e) => setSelectedSearchAPI(e.target.value)}
                    className="select"
                  >
                    {searchAPIs.map((api) => (
                      <option key={api.id} value={api.id}>
                        {api.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {searchAPIs.find(api => api.id === selectedSearchAPI)?.description}
                  </p>
                </div>

                {/* Research Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Research Model
                  </label>
                  <select
                    value={selectedResearchModel}
                    onChange={(e) => setSelectedResearchModel(e.target.value)}
                    className="select"
                  >
                    {models.map((model) => (
                      <option key={model} value={model}>
                        {model.replace('openai:', '')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Summarization Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Summarization Model
                  </label>
                  <select
                    value={selectedSummarizationModel}
                    onChange={(e) => setSelectedSummarizationModel(e.target.value)}
                    className="select"
                  >
                    {models.map((model) => (
                      <option key={model} value={model}>
                        {model.replace('openai:', '')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Max Iterations */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Researcher Iterations: {maxIterations}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="15"
                    value={maxIterations}
                    onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* Max Concurrent Units */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Concurrent Research Units: {maxConcurrentUnits}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={maxConcurrentUnits}
                    onChange={(e) => setMaxConcurrentUnits(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* Allow Clarification */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="clarification"
                    checked={allowClarification}
                    onChange={(e) => setAllowClarification(e.target.checked)}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <label htmlFor="clarification" className="ml-2 text-sm font-medium text-gray-700">
                    Allow clarification questions
                  </label>
                </div>

                {/* Export Formats */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Export Formats
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {exportFormats.map((format) => (
                      <button
                        key={format.id}
                        type="button"
                        onClick={() => toggleExportFormat(format.id)}
                        className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                          selectedExportFormats.includes(format.id)
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-primary-600'
                        }`}
                      >
                        {format.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="mt-6">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              <Search className="w-5 h-5" />
              <span>{isLoading ? 'Starting Research...' : 'Start Research'}</span>
            </button>
          </div>
        </form>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Search className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Multi-Source Search</h3>
            <p className="text-sm text-gray-600">
              Search across ArXiv, Semantic Scholar, and web sources
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">AI-Powered Analysis</h3>
            <p className="text-sm text-gray-600">
              Advanced AI agents synthesize and analyze research findings
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Multiple Export Formats</h3>
            <p className="text-sm text-gray-600">
              Export to PDF, DOCX, HTML, Markdown, and more
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
