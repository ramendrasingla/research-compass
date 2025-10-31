import React from 'react';
import { X, CheckCircle, Loader2, XCircle, Search, ExternalLink } from 'lucide-react';

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

interface ResearchDetailModalProps {
  topic: ResearchTopicNode | null;
  onClose: () => void;
}

const ResearchDetailModal: React.FC<ResearchDetailModalProps> = ({ topic, onClose }) => {
  if (!topic) return null;

  const getStatusInfo = () => {
    switch (topic.status) {
      case 'active':
        return {
          icon: <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />,
          text: 'Research in Progress',
          color: 'text-blue-600',
          bg: 'bg-blue-50',
        };
      case 'completed':
        return {
          icon: <CheckCircle className="w-5 h-5 text-green-600" />,
          text: 'Research Completed',
          color: 'text-green-600',
          bg: 'bg-green-50',
        };
      case 'error':
        return {
          icon: <XCircle className="w-5 h-5 text-red-600" />,
          text: 'Research Failed',
          color: 'text-red-600',
          bg: 'bg-red-50',
        };
      default:
        return {
          icon: <Search className="w-5 h-5 text-gray-600" />,
          text: 'Pending',
          color: 'text-gray-600',
          bg: 'bg-gray-50',
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {statusInfo.icon}
                <h2 className="text-lg font-semibold text-gray-900">Research Details</h2>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-1 rounded ${statusInfo.bg} ${statusInfo.color} font-medium`}>
                  {statusInfo.text}
                </span>
                {topic.searchApi && (
                  <span className="px-2 py-1 bg-gray-100 rounded text-gray-700 capitalize">
                    {topic.searchApi}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-140px)]">
            {/* Research Topic */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Research Topic</h3>
              <p className="text-gray-900">{topic.topic}</p>
            </div>

            {/* Timeline */}
            {(topic.startTime || topic.endTime) && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Timeline</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  {topic.startTime && (
                    <div>Started: {topic.startTime.toLocaleString()}</div>
                  )}
                  {topic.endTime && (
                    <div>Completed: {topic.endTime.toLocaleString()}</div>
                  )}
                  {topic.startTime && topic.endTime && (
                    <div className="text-xs text-gray-500">
                      Duration: {Math.round((topic.endTime.getTime() - topic.startTime.getTime()) / 1000)}s
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Sources */}
            {topic.sources && topic.sources.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Sources ({topic.sources.length})
                </h3>
                <div className="space-y-2">
                  {topic.sources.map((source, idx) => {
                    const isUrl = source.startsWith('http');
                    return (
                      <div key={idx} className="p-3 bg-gray-50 rounded border border-gray-200">
                        {isUrl ? (
                          <a
                            href={source}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 hover:underline"
                          >
                            <ExternalLink className="w-4 h-4 flex-shrink-0" />
                            <span className="break-all">{source}</span>
                          </a>
                        ) : (
                          <div className="text-sm text-gray-700">{source}</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Findings */}
            {topic.findings && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Research Findings</h3>
                <div className="p-4 bg-green-50 border border-green-200 rounded">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{topic.findings}</p>
                </div>
              </div>
            )}

            {/* Status Message */}
            {topic.status === 'active' && !topic.findings && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded">
                <div className="flex items-center gap-2 text-sm text-blue-700">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Research is currently in progress. Findings will appear here when available.</span>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4">
            <button
              onClick={onClose}
              className="btn-primary w-full sm:w-auto"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchDetailModal;
