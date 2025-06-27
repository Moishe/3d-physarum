// ABOUTME: Enhanced model history component showing both active jobs and persistent model history
// ABOUTME: Unified interface for managing simulation results with favorites, filtering, and downloads

import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import type { SimulationResult } from '../types/simulation';
import { api, type ModelRecord } from '../services/api';

// Unified history item type that can represent both active jobs and persistent models
interface HistoryItem {
  id: string;
  name: string;
  jobId?: string; // For active jobs
  modelId?: string; // For persistent models
  createdAt: string;
  downloadedAt?: string;
  viewedAt?: string;
  favorite: boolean;
  parameters: any;
  fileSize: number;
  source: 'active' | 'cli' | 'web' | 'unknown';
  stlPath?: string;
  jsonPath?: string;
  previewPath?: string;
  tags: string[];
}

interface ModelHistoryProps {
  onLoadParameters?: (parameters: any) => void;
  onNewSimulation?: () => void;
  className?: string;
}

const ModelHistory = forwardRef<{ addToHistory: (result: SimulationResult) => void }, ModelHistoryProps>(({ 
  onLoadParameters, 
  onNewSimulation, 
  className = '' 
}, ref) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filter, setFilter] = useState<'all' | 'favorites' | 'recent' | 'cli' | 'web'>('all');
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Load unified history from both localStorage and model registry
  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Load persistent models from registry
      const modelsResponse = await api.listModels({ limit: 50 });
      const persistentModels: HistoryItem[] = modelsResponse.data.models.map(model => ({
        id: model.id,
        modelId: model.id,
        name: model.name,
        createdAt: new Date(model.created_at * 1000).toISOString(),
        favorite: model.favorite,
        parameters: model.parameters,
        fileSize: model.file_sizes.stl || 0,
        source: model.source as 'cli' | 'web' | 'unknown',
        stlPath: model.stl_path ? api.getModelDownloadUrl(model.id, 'stl') : undefined,
        jsonPath: model.json_path ? api.getModelDownloadUrl(model.id, 'json') : undefined,
        previewPath: model.jpg_path ? api.getModelDownloadUrl(model.id, 'preview') : undefined,
        tags: model.tags
      }));
      
      // Load legacy localStorage history for active jobs
      const savedHistory = localStorage.getItem('physarum-download-history');
      let legacyHistory: HistoryItem[] = [];
      if (savedHistory) {
        try {
          const parsed = JSON.parse(savedHistory);
          legacyHistory = parsed
            .filter((item: any) => !persistentModels.find(pm => pm.jobId === item.jobId))
            .map((item: any) => ({
              id: item.jobId || `legacy_${Date.now()}_${Math.random()}`,
              jobId: item.jobId,
              name: item.parameters?.output || 'Untitled Model',
              createdAt: item.completedAt || item.downloadedAt || new Date().toISOString(),
              downloadedAt: item.downloadedAt,
              favorite: item.favorite || false,
              parameters: item.parameters || {},
              fileSize: item.fileSize || 0,
              source: 'active' as const,
              stlPath: item.stlPath,
              jsonPath: item.jsonPath,
              previewPath: item.previewPath,
              tags: []
            }));
        } catch (error) {
          console.error('Failed to parse legacy download history:', error);
        }
      }
      
      // Combine and sort by creation date
      const allHistory = [...persistentModels, ...legacyHistory].sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      
      setHistory(allHistory);
    } catch (error) {
      console.error('Failed to load model history:', error);
      setError(error instanceof Error ? error.message : 'Failed to load model history');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Initial load
  useEffect(() => {
    loadHistory();
  }, []);
  
  const addToHistory = async (result: SimulationResult) => {
    // For new active jobs, add to both localStorage and potentially trigger registry rescan
    const historyItem: HistoryItem = {
      id: result.jobId,
      jobId: result.jobId,
      name: result.parameters?.output || 'Untitled Model',
      createdAt: result.completedAt,
      downloadedAt: new Date().toISOString(),
      favorite: false,
      parameters: result.parameters,
      fileSize: result.fileSize,
      source: 'active',
      stlPath: result.stlPath,
      jsonPath: result.jsonPath,
      previewPath: result.previewPath,
      tags: []
    };
    
    // Update localStorage for backward compatibility
    const savedHistory = localStorage.getItem('physarum-download-history');
    let existingHistory = [];
    if (savedHistory) {
      try {
        existingHistory = JSON.parse(savedHistory);
      } catch (error) {
        console.error('Failed to parse existing history:', error);
      }
    }
    
    // Remove duplicate if exists and add new item
    const filtered = existingHistory.filter((item: any) => item.jobId !== result.jobId);
    const newHistory = [result, ...filtered].slice(0, 20);
    localStorage.setItem('physarum-download-history', JSON.stringify(newHistory));
    
    // Reload the unified history
    await loadHistory();
  };
  
  // Expose addToHistory method for parent components
  useImperativeHandle(ref, () => ({
    addToHistory
  }));
  
  const toggleFavorite = async (item: HistoryItem) => {
    if (item.modelId) {
      // Update persistent model
      try {
        await api.updateModel(item.modelId, { favorite: !item.favorite });
        await loadHistory(); // Refresh
      } catch (error) {
        console.error('Failed to update favorite status:', error);
      }
    } else {
      // Update localStorage for active jobs
      setHistory(prev => prev.map(histItem => 
        histItem.id === item.id 
          ? { ...histItem, favorite: !histItem.favorite }
          : histItem
      ));
    }
  };
  
  const clearHistory = async () => {
    // Only clear localStorage history, keep persistent models
    localStorage.removeItem('physarum-download-history');
    await loadHistory();
  };
  
  const refreshHistory = async () => {
    await loadHistory();
  };
  
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };
  
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };
  
  const getFilteredHistory = () => {
    switch (filter) {
      case 'favorites':
        return history.filter(item => item.favorite);
      case 'recent':
        return history.filter(item => {
          const itemDate = new Date(item.createdAt);
          const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
          return itemDate > weekAgo;
        });
      case 'cli':
        return history.filter(item => item.source === 'cli');
      case 'web':
        return history.filter(item => item.source === 'web' || item.source === 'active');
      default:
        return history;
    }
  };
  
  const getSourceBadge = (source: string) => {
    const badges = {
      'cli': { color: 'bg-green-100 text-green-800', label: 'CLI' },
      'web': { color: 'bg-blue-100 text-blue-800', label: 'Web' },
      'active': { color: 'bg-purple-100 text-purple-800', label: 'Active' },
      'unknown': { color: 'bg-gray-100 text-gray-800', label: 'Unknown' }
    };
    const badge = badges[source as keyof typeof badges] || badges.unknown;
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.label}
      </span>
    );
  };
  
  const filteredHistory = getFilteredHistory();
  
  if (isLoading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 text-center ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading model history...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 text-center ${className}`}>
        <svg className="mx-auto h-12 w-12 text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.232 13.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <h3 className="text-lg font-medium text-red-900 mb-2">Failed to Load History</h3>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={refreshHistory}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }
  
  if (history.length === 0) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-6 text-center ${className}`}>
        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Model History</h3>
        <p className="text-gray-600 mb-4">
          Your generated models will appear here for easy re-download and parameter reference.
        </p>
        {onNewSimulation && (
          <button
            onClick={onNewSimulation}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Generate Your First Model
          </button>
        )}
      </div>
    );
  }
  
  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h3 className="text-lg font-medium text-gray-900">Model History</h3>
            <span className="ml-2 bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
              {history.length}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Filter Buttons */}
            <div className="flex bg-gray-100 rounded-md p-1">
              {[
                ['all', 'All'], 
                ['recent', 'Recent'], 
                ['favorites', 'Favorites'],
                ['cli', 'CLI'],
                ['web', 'Web']
              ].map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => setFilter(value as any)}
                  className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                    filter === value
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            
            {/* Refresh Button */}
            <button
              onClick={refreshHistory}
              className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
              title="Refresh History"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
              </svg>
            </button>
            
            {/* Clear History */}
            {history.some(item => item.source === 'active') && (
              <button
                onClick={clearHistory}
                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                title="Clear Active Job History"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* History List */}
      <div className="max-h-96 overflow-y-auto">
        {filteredHistory.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No items match the current filter.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredHistory.slice(0, isExpanded ? undefined : 5).map((item) => (
              <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {item.name}
                      </h4>
                      
                      {/* Source Badge */}
                      <div className="ml-2">
                        {getSourceBadge(item.source)}
                      </div>
                      
                      {/* Favorite Star */}
                      <button
                        onClick={() => toggleFavorite(item)}
                        className={`ml-2 p-1 ${
                          item.favorite 
                            ? 'text-yellow-400 hover:text-yellow-500' 
                            : 'text-gray-300 hover:text-yellow-400'
                        } transition-colors`}
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </button>
                    </div>
                    
                    <div className="mt-1 flex items-center space-x-3 text-xs text-gray-500">
                      <span>{formatDate(item.createdAt)}</span>
                      <span>{formatFileSize(item.fileSize)}</span>
                      <span>{item.parameters.width}×{item.parameters.height}</span>
                      <span className="hidden sm:inline">{item.parameters.actors} actors</span>
                      {item.parameters.smooth && <span className="text-blue-600 hidden sm:inline">Smooth</span>}
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex items-center space-x-1 ml-4">
                    {/* Load Parameters */}
                    {onLoadParameters && (
                      <button
                        onClick={() => onLoadParameters(item.parameters)}
                        className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                        title="Use These Parameters"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                        </svg>
                      </button>
                    )}
                    
                    {/* Download STL */}
                    {item.stlPath && (
                      <button
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = item.stlPath!;
                          link.download = `${item.name}.stl`;
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Download STL"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Show More/Less Button */}
            {filteredHistory.length > 5 && (
              <div className="p-4 text-center border-t border-gray-200">
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  {isExpanded ? 'Show Less' : `Show ${filteredHistory.length - 5} More`}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

ModelHistory.displayName = 'ModelHistory';
export default ModelHistory;