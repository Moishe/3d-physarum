// ABOUTME: Progress display component showing real-time simulation status and statistics
// ABOUTME: Displays current step, layer count, actor count, trail stats, and estimated time remaining

import type { SimulationStatus as StatusType } from '../types/simulation';

interface SimulationStatusProps {
  status: StatusType | null;
  onCancel?: () => void;
}

export default function SimulationStatus({ status, onCancel }: SimulationStatusProps) {
  if (!status) {
    return null;
  }

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const getStatusColor = (status: StatusType['status']) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'cancelled':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: StatusType['status']) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'running':
        return 'Running';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'cancelled':
        return 'Cancelled';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-medium text-gray-900">Simulation Status</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status.status)}`}>
                {getStatusText(status.status)}
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Job ID: {status.jobId}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        {status.status === 'running' && (
          <div className="px-6 py-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{status.progress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Statistics Grid */}
        <div className="px-6 py-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Current Step */}
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {status.currentStep.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Current Step</div>
              <div className="text-xs text-gray-400">
                of {status.totalSteps.toLocaleString()}
              </div>
            </div>

            {/* Captured Layers */}
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {status.capturedLayers}
              </div>
              <div className="text-sm text-gray-500">Layers Captured</div>
            </div>

            {/* Actor Count */}
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {status.actorCount.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Active Actors</div>
            </div>

            {/* Estimated Time */}
            {status.estimatedTimeRemaining && status.status === 'running' && (
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {formatTime(status.estimatedTimeRemaining)}
                </div>
                <div className="text-sm text-gray-500">Est. Remaining</div>
              </div>
            )}
          </div>
        </div>

        {/* Trail Statistics */}
        <div className="px-6 py-4 border-t border-gray-200">
          <h4 className="text-md font-medium text-gray-900 mb-3">Trail Statistics</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Maximum Trail Strength:</span>
              <span className="text-sm font-medium text-gray-900">
                {status.trailStats.maxTrail.toFixed(3)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Average Trail Strength:</span>
              <span className="text-sm font-medium text-gray-900">
                {status.trailStats.meanTrail.toFixed(3)}
              </span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {status.error && (
          <div className="px-6 py-4 border-t border-gray-200">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Simulation Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{status.error}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {status.status === 'running' && onCancel && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
            <div className="flex justify-end">
              <button
                onClick={onCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Cancel Simulation
              </button>
            </div>
          </div>
        )}

        {/* Loading Animation for Running Status */}
        {status.status === 'running' && (
          <div className="absolute top-2 right-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          </div>
        )}
      </div>

      {/* Status Messages */}
      {status.status === 'pending' && (
        <div className="mt-4 text-center text-gray-600">
          <div className="animate-pulse">
            Waiting for simulation to start...
          </div>
        </div>
      )}

      {status.status === 'completed' && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-md">
            <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Simulation completed successfully!
          </div>
        </div>
      )}
    </div>
  );
}