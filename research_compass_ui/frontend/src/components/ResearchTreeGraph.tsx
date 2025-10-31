import React, { useState } from 'react';
import { CheckCircle, Circle, Loader2, XCircle, Brain, ChevronDown, ChevronUp } from 'lucide-react';

interface ResearchTopicNode {
  id: string;
  topic: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  iteration?: number;
  startTime?: Date;
  endTime?: Date;
  findings?: string;
  sources?: string[];
  searchApi?: string;
}

interface ResearchTreeGraphProps {
  supervisorStatus: 'idle' | 'thinking' | 'delegating' | 'completed';
  currentIteration: number;
  maxIterations: number;
  researchTopics: ResearchTopicNode[];
  compact?: boolean;
  onTopicClick?: (topic: ResearchTopicNode) => void;
}

const ResearchTreeGraph: React.FC<ResearchTreeGraphProps> = ({
  supervisorStatus,
  currentIteration: _currentIteration,
  maxIterations: _maxIterations,
  researchTopics,
  compact = false,
  onTopicClick,
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'active':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getSupervisorStatusText = () => {
    switch (supervisorStatus) {
      case 'thinking':
        return 'Analyzing research strategy...';
      case 'delegating':
        return 'Delegating research tasks...';
      case 'completed':
        return 'Research supervision completed';
      default:
        return 'Idle';
    }
  };

  const getSupervisorIcon = () => {
    if (supervisorStatus === 'thinking' || supervisorStatus === 'delegating') {
      return <Loader2 className="w-6 h-6 text-purple-600 animate-spin" />;
    }
    return <Brain className="w-6 h-6 text-purple-600" />;
  };

  const activeTopics = researchTopics.filter(t => t.status === 'active').length;
  const completedTopics = researchTopics.filter(t => t.status === 'completed').length;

  // Compact summary view
  if (compact && !isExpanded) {
    // Show even when there are no topics yet
    const statusText = researchTopics.length === 0
      ? 'Planning research strategy...'
      : supervisorStatus === 'completed'
        ? 'Research Completed'
        : 'Research In Progress'

    return (
      <div className="mt-3 pl-8">
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full text-left flex items-center justify-between p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200"
        >
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-blue-600" />
            <div>
              <div className="text-sm font-medium text-gray-800">
                {statusText}
              </div>
              {researchTopics.length > 0 ? (
                <div className="text-xs text-gray-600 flex items-center gap-3 mt-1">
                  <span className="flex items-center gap-1">
                    <Loader2 className="w-3 h-3 text-blue-600" />
                    {activeTopics} active
                  </span>
                  <span className="flex items-center gap-1">
                    <CheckCircle className="w-3 h-3 text-green-600" />
                    {completedTopics} completed
                  </span>
                </div>
              ) : (
                <div className="text-xs text-gray-600 mt-1">
                  Click to see details when available
                </div>
              )}
            </div>
          </div>
          <ChevronDown className="w-5 h-5 text-gray-400" />
        </button>
      </div>
    );
  }

  return (
    <div className={compact ? "mt-3 pl-8" : "bg-white rounded-lg shadow-md p-6"}>
      {compact && (
        <button
          onClick={() => setIsExpanded(false)}
          className="w-full text-left flex items-center justify-between p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200 mb-4"
        >
          <div className="flex items-center gap-3">
            <Brain className="w-5 h-5 text-blue-600" />
            <div>
              <div className="text-sm font-medium text-gray-800">
                {supervisorStatus === 'completed' ? 'Research Completed' : 'Research In Progress'}
              </div>
              <div className="text-xs text-gray-600 flex items-center gap-3 mt-1">
                <span className="flex items-center gap-1">
                  <Loader2 className="w-3 h-3 text-blue-600" />
                  {activeTopics} active
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-green-600" />
                  {completedTopics} completed
                </span>
              </div>
            </div>
          </div>
          <ChevronUp className="w-5 h-5 text-gray-400" />
        </button>
      )}

      {!compact && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Research Progress Tree</h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>Active: {activeTopics}</span>
            <span>Completed: {completedTopics}</span>
          </div>
        </div>
      )}

      {/* Supervisor Node */}
      {!compact && (
        <div className="flex flex-col items-center mb-8">
          <div className={`
            relative flex items-center gap-3 px-6 py-4 rounded-lg border-2
            ${supervisorStatus === 'thinking' || supervisorStatus === 'delegating'
              ? 'border-purple-500 bg-purple-50'
              : 'border-purple-300 bg-purple-50'
            }
            shadow-lg
          `}>
            {getSupervisorIcon()}
            <div>
              <div className="font-semibold text-gray-800">Research Supervisor</div>
              <div className="text-sm text-gray-600">{getSupervisorStatusText()}</div>
            </div>
          </div>

          {/* Connector Line */}
          {researchTopics.length > 0 && (
            <div className="w-0.5 h-8 bg-gray-300 my-2"></div>
          )}
        </div>
      )}

      {/* Research Topics Grid */}
      {researchTopics.length > 0 ? (
        <div className={compact ? "space-y-3" : "relative"}>
          {/* Horizontal Branch Line - only for non-compact */}
          {!compact && researchTopics.length > 1 && (
            <div
              className="absolute left-0 right-0 h-0.5 bg-gray-300"
              style={{ top: '20px' }}
            ></div>
          )}

          {/* Topics Grid - different layout for compact */}
          <div className={compact ? "space-y-2" : "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"}>
            {researchTopics.map((topic) => (
              <div key={topic.id} className={compact ? "" : "flex flex-col items-center"}>
                {/* Vertical connector to horizontal line - only for non-compact */}
                {!compact && researchTopics.length > 1 && (
                  <div className="w-0.5 h-8 bg-gray-300 mb-2"></div>
                )}

                {/* Topic Node */}
                <button
                  onClick={() => onTopicClick?.(topic)}
                  className={`
                  w-full p-3 rounded-lg border transition-all text-left
                  ${topic.status === 'active'
                    ? 'border-blue-400 bg-blue-50 hover:bg-blue-100'
                    : topic.status === 'completed'
                    ? 'border-green-400 bg-green-50 hover:bg-green-100'
                    : topic.status === 'error'
                    ? 'border-red-400 bg-red-50 hover:bg-red-100'
                    : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
                  }
                  ${onTopicClick ? 'cursor-pointer' : 'cursor-default'}
                `}>
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0">
                      {getStatusIcon(topic.status)}
                    </div>
                    <div className="flex-grow min-w-0">
                      {topic.searchApi && (
                        <div className="flex items-center justify-end gap-2 mb-2">
                          <span className="text-xs px-2 py-0.5 bg-white rounded border border-gray-300 text-gray-600 capitalize">
                            {topic.searchApi}
                          </span>
                        </div>
                      )}
                      <div className="text-sm text-gray-800 mb-2 line-clamp-2">
                        {topic.topic}
                      </div>

                      {/* Sources - compact display */}
                      {topic.sources && topic.sources.length > 0 && (
                        <div className="text-xs text-gray-500 mb-2">
                          <span className="font-medium">{topic.sources.length} source{topic.sources.length > 1 ? 's' : ''}</span>
                          {compact && topic.sources.length > 0 && (
                            <span className="ml-1">• {topic.sources[0].length > 40 ? topic.sources[0].substring(0, 40) + '...' : topic.sources[0]}</span>
                          )}
                        </div>
                      )}

                      {topic.status === 'active' && (
                        <div className="text-xs text-blue-600 flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          Researching...
                        </div>
                      )}
                      {topic.status === 'completed' && (
                        <div className="text-xs text-green-600 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Completed
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-6">
          <Loader2 className="w-8 h-8 mx-auto mb-2 text-blue-400 animate-spin" />
          <p className="text-sm">Research supervisor is planning the investigation strategy...</p>
          <p className="text-xs text-gray-400 mt-1">Topics will appear here as they are delegated</p>
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Circle className="w-4 h-4 text-gray-400" />
            <span>Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-blue-600" />
            <span>Active</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-600" />
            <span>Error</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchTreeGraph;
