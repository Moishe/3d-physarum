// ABOUTME: Component for displaying completed simulation results with download options
// ABOUTME: Shows STL download, preview image, model statistics, and parameters used

import type { SimulationResult } from '../types/simulation';

interface ResultsDisplayProps {
  result: SimulationResult | null;
  onNewSimulation?: () => void;
}

export default function ResultsDisplay({ result, onNewSimulation }: ResultsDisplayProps) {
  if (!result) {
    return null;
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    } else if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    } else {
      return `${bytes} bytes`;
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const downloadFile = (path: string, filename: string) => {
    const link = document.createElement('a');
    link.href = path;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Simulation Results</h3>
              <p className="text-sm text-gray-500">Generated on {formatDate(result.completedAt)}</p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Complete
              </span>
            </div>
          </div>
        </div>

        {/* Preview Image */}
        <div className="px-6 py-4">
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="flex-1">
              <h4 className="text-md font-medium text-gray-900 mb-3">Preview Image</h4>
              <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center min-h-64">
                <img
                  src={result.previewPath}
                  alt="3D Model Preview"
                  className="max-w-full max-h-64 rounded-lg shadow-sm"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    target.nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <div className="hidden text-gray-500 text-center">
                  <svg className="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p>Preview image not available</p>
                </div>
              </div>
            </div>

            {/* Download Section */}
            <div className="flex-1">
              <h4 className="text-md font-medium text-gray-900 mb-3">Download Files</h4>
              <div className="space-y-3">
                {/* STL File */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="font-medium text-gray-900">3D Model (STL)</h5>
                      <p className="text-sm text-gray-500">
                        {result.stlPath.split('/').pop()} • {formatFileSize(result.fileSize)}
                      </p>
                    </div>
                    <button
                      onClick={() => downloadFile(result.stlPath, result.stlPath.split('/').pop() || 'model.stl')}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download
                    </button>
                  </div>
                </div>

                {/* Parameters JSON */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="font-medium text-gray-900">Parameters (JSON)</h5>
                      <p className="text-sm text-gray-500">
                        {result.jsonPath.split('/').pop()}
                      </p>
                    </div>
                    <button
                      onClick={() => downloadFile(result.jsonPath, result.jsonPath.split('/').pop() || 'parameters.json')}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download
                    </button>
                  </div>
                </div>

                {/* Preview Image */}
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="font-medium text-gray-900">Preview Image</h5>
                      <p className="text-sm text-gray-500">
                        {result.previewPath.split('/').pop()}
                      </p>
                    </div>
                    <button
                      onClick={() => downloadFile(result.previewPath, result.previewPath.split('/').pop() || 'preview.jpg')}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Model Statistics */}
        {result.meshMetrics && (
          <div className="px-6 py-4 border-t border-gray-200">
            <h4 className="text-md font-medium text-gray-900 mb-3">Model Statistics</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {result.meshMetrics.vertexCount.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Vertices</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {result.meshMetrics.faceCount.toLocaleString()}
                </div>
                <div className="text-sm text-gray-500">Faces</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {result.meshMetrics.volume.toFixed(2)}
                </div>
                <div className="text-sm text-gray-500">Volume</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {result.meshMetrics.surfaceArea.toFixed(2)}
                </div>
                <div className="text-sm text-gray-500">Surface Area</div>
              </div>
            </div>

            {/* Quality Indicators */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Watertight</span>
                <span className={`text-sm font-bold ${result.meshMetrics.isWatertight ? 'text-green-600' : 'text-red-600'}`}>
                  {result.meshMetrics.isWatertight ? '✓' : '✗'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Winding Consistent</span>
                <span className={`text-sm font-bold ${result.meshMetrics.isWindingConsistent ? 'text-green-600' : 'text-red-600'}`}>
                  {result.meshMetrics.isWindingConsistent ? '✓' : '✗'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">3D Print Ready</span>
                <span className={`text-sm font-bold ${result.meshMetrics.printReady ? 'text-green-600' : 'text-red-600'}`}>
                  {result.meshMetrics.printReady ? '✓' : '✗'}
                </span>
              </div>
            </div>

            {/* Issues */}
            {result.meshMetrics.issues.length > 0 && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h5 className="font-medium text-yellow-800 mb-2">Model Issues</h5>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {result.meshMetrics.issues.map((issue, index) => (
                    <li key={index} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Parameters Summary */}
        <div className="px-6 py-4 border-t border-gray-200">
          <h4 className="text-md font-medium text-gray-900 mb-3">Parameters Used</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Grid Size:</span>
              <span className="ml-2 text-gray-900">{result.parameters.width}×{result.parameters.height}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Actors:</span>
              <span className="ml-2 text-gray-900">{result.parameters.actors}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Steps:</span>
              <span className="ml-2 text-gray-900">{result.parameters.steps}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Model Type:</span>
              <span className="ml-2 text-gray-900">{result.parameters.smooth ? 'Smooth' : 'Voxel'}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Decay Rate:</span>
              <span className="ml-2 text-gray-900">{result.parameters.decay}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Threshold:</span>
              <span className="ml-2 text-gray-900">{result.parameters.threshold}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Layer Height:</span>
              <span className="ml-2 text-gray-900">{result.parameters.layerHeight}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Speed:</span>
              <span className="ml-2 text-gray-900">{result.parameters.speed}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
          <div className="flex justify-between">
            <button
              onClick={() => downloadFile(result.stlPath, result.stlPath.split('/').pop() || 'model.stl')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download STL
            </button>
            {onNewSimulation && (
              <button
                onClick={onNewSimulation}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                New Simulation
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}