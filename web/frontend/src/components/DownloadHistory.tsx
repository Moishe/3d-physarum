// ABOUTME: Download history component displaying recent simulation results with quick access
// ABOUTME: Manages local storage of simulation history and provides filtering and download actions

import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import type { SimulationResult } from '../types/simulation';
import { api } from '../services/api';

interface HistoryItem extends SimulationResult {
  downloadedAt?: string;
  viewedAt?: string;
  favorite?: boolean;
}

interface DownloadHistoryProps {
  onLoadParameters?: (parameters: any) => void;
  onNewSimulation?: () => void;
  className?: string;
}

const DownloadHistory = forwardRef<{ addToHistory: (result: SimulationResult) => void }, DownloadHistoryProps>(({ 
  onLoadParameters, 
  onNewSimulation, 
  className = '' 
}, ref) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [filter, setFilter] = useState<'all' | 'favorites' | 'recent'>('all');
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('physarum-download-history');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setHistory(parsed);
      } catch (error) {
        console.error('Failed to parse download history:', error);
      }
    }
  }, []);
  
  // Save history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('physarum-download-history', JSON.stringify(history));
  }, [history]);
  
  const addToHistory = (result: SimulationResult) => {
    const historyItem: HistoryItem = {
      ...result,
      downloadedAt: new Date().toISOString(),
    };
    
    setHistory(prev => {
      // Remove duplicate if exists
      const filtered = prev.filter(item => item.jobId !== result.jobId);
      // Add new item at the beginning
      const newHistory = [historyItem, ...filtered];
      // Keep only last 20 items
      return newHistory.slice(0, 20);
    });
  };
  
  // Expose addToHistory method for parent components
  useImperativeHandle(ref, () => ({
    addToHistory
  }));
  
  const toggleFavorite = (jobId: string) => {
    setHistory(prev => prev.map(item => 
      item.jobId === jobId 
        ? { ...item, favorite: !item.favorite }
        : item
    ));
  };
  
  const clearHistory = () => {
    setHistory([]);
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
          const itemDate = new Date(item.completedAt);
          const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
          return itemDate > weekAgo;
        });
      default:
        return history;
    }
  };
  
  const filteredHistory = getFilteredHistory();
  
  if (history.length === 0) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-6 text-center ${className}`}>
        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Download History</h3>
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
            <h3 className="text-lg font-medium text-gray-900">Download History</h3>
            <span className="ml-2 bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
              {history.length}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Filter Buttons */}
            <div className="flex bg-gray-100 rounded-md p-1">
              {[['all', 'All'], ['recent', 'Recent'], ['favorites', 'Favorites']].map(([value, label]) => (
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
            
            {/* Clear History */}
            {history.length > 0 && (
              <button
                onClick={clearHistory}
                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                title="Clear History"
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
            {filteredHistory.slice(0, isExpanded ? undefined : 3).map((item) => (
              <div key={item.jobId} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {item.parameters.output || 'Untitled Model'}
                      </h4>
                      
                      {/* Favorite Star */}
                      <button
                        onClick={() => toggleFavorite(item.jobId)}
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
                      <span>{formatDate(item.completedAt)}</span>
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
                    <button
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = api.getDownloadUrl(item.jobId, 'stl');
                        link.download = item.stlPath.split('/').pop() || 'model.stl';
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
                  </div>
                </div>
              </div>
            ))}
            
            {/* Show More/Less Button */}
            {filteredHistory.length > 3 && (
              <div className="p-4 text-center border-t border-gray-200">
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  {isExpanded ? 'Show Less' : `Show ${filteredHistory.length - 3} More`}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

DownloadHistory.displayName = 'DownloadHistory';
export default DownloadHistory;