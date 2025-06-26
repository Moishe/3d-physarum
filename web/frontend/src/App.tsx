// ABOUTME: Main application component that orchestrates the 3D Physarum model generation workflow
// ABOUTME: Manages simulation state and coordinates between parameter form, status display, and results

import { useState, useRef } from 'react';
import ParameterForm from './components/ParameterForm';
import SimulationStatus from './components/SimulationStatus';
import ResultsDisplay from './components/ResultsDisplay';
import ErrorDisplay from './components/ErrorDisplay';
import DownloadHistory from './components/DownloadHistory';
import type { SimulationParameters, SimulationStatus as StatusType, SimulationResult } from './types/simulation';
import { PARAMETER_PRESETS } from './types/simulation';
import { api } from './services/api';
import './App.css';

function App() {
  const [currentStatus, setCurrentStatus] = useState<StatusType | null>(null);
  const [currentResult, setCurrentResult] = useState<SimulationResult | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentError, setCurrentError] = useState<Error | string | null>(null);
  const [formParameters, setFormParameters] = useState<Partial<SimulationParameters>>({});
  const historyRef = useRef<any>(null);

  const startSimulation = async (parameters: SimulationParameters) => {
    setIsSimulating(true);
    setCurrentResult(null);
    setCurrentError(null);
    
    try {
      // Start the simulation
      const { jobId } = await api.startSimulation(parameters);
      
      // Create initial status
      const initialStatus: StatusType = {
        jobId,
        status: 'pending',
        currentStep: 0,
        totalSteps: parameters.steps,
        capturedLayers: 0,
        actorCount: parameters.actors,
        trailStats: {
          maxTrail: 0,
          meanTrail: 0,
        },
        progress: 0,
      };
      
      setCurrentStatus(initialStatus);

      // Poll for status updates
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getSimulationStatus(jobId);
          setCurrentStatus(status);
          
          // If simulation is completed, get the result
          if (status.status === 'completed') {
            clearInterval(pollInterval);
            try {
              const result = await api.getSimulationResult(jobId);
              setCurrentResult(result);
              setIsSimulating(false);
              
              // Add to download history
              if (historyRef.current && historyRef.current.addToHistory) {
                historyRef.current.addToHistory(result);
              }
            } catch (resultError) {
              console.error('Error fetching result:', resultError);
              setCurrentError(resultError instanceof Error ? resultError : new Error(String(resultError)));
              setIsSimulating(false);
            }
          }
          
          // If simulation failed or was cancelled, stop polling
          if (status.status === 'failed' || status.status === 'cancelled') {
            clearInterval(pollInterval);
            setIsSimulating(false);
            if (status.status === 'failed' && status.error) {
              setCurrentError(new Error(status.error));
            }
          }
        } catch (statusError) {
          console.error('Error polling status:', statusError);
          // Continue polling on status errors to handle temporary network issues
        }
      }, 2000); // Poll every 2 seconds

      // Set a timeout to stop polling after a reasonable time
      setTimeout(() => {
        clearInterval(pollInterval);
        if (isSimulating) {
          setCurrentError(new Error('Simulation timed out'));
          setIsSimulating(false);
        }
      }, 30 * 60 * 1000); // 30 minutes timeout

    } catch (error) {
      console.error('Simulation error:', error);
      setCurrentError(error instanceof Error ? error : new Error(String(error)));
      setCurrentStatus(prev => prev ? {
        ...prev,
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
      } : null);
      setIsSimulating(false);
    }
  };

  const handleCancel = async () => {
    if (currentStatus?.jobId) {
      try {
        await api.cancelSimulation(currentStatus.jobId);
        setCurrentStatus(prev => prev ? {
          ...prev,
          status: 'cancelled',
        } : null);
        setIsSimulating(false);
      } catch (error) {
        console.error('Error cancelling simulation:', error);
        setCurrentError(error instanceof Error ? error : new Error(String(error)));
      }
    }
  };

  const handleNewSimulation = () => {
    setCurrentStatus(null);
    setCurrentResult(null);
    setIsSimulating(false);
    setCurrentError(null);
  };
  
  const handleErrorRetry = () => {
    setCurrentError(null);
    // Reset to allow new simulation
    setCurrentStatus(null);
    setCurrentResult(null);
    setIsSimulating(false);
  };
  
  const handleErrorUsePreset = () => {
    setCurrentError(null);
    // Reset and scroll to presets
    setCurrentStatus(null);
    setCurrentResult(null);
    setIsSimulating(false);
    // Scroll to top where presets are
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  
  const handleErrorSimplify = () => {
    setCurrentError(null);
    // Apply fast preview preset automatically
    const fastPreset = PARAMETER_PRESETS.find(p => p.name === 'Fast Preview');
    if (fastPreset) {
      // This would need to be passed down to the form
      console.log('Would apply fast preset:', fastPreset);
    }
    setCurrentStatus(null);
    setCurrentResult(null);
    setIsSimulating(false);
  };
  
  const handleErrorRefresh = () => {
    window.location.reload();
  };
  
  const handleErrorContactSupport = () => {
    // Open support email or form
    const subject = encodeURIComponent('Physarum 3D Generator Error Report');
    const body = encodeURIComponent(
      `I encountered an error while using the Physarum 3D Generator:\n\n` +
      `Error: ${currentError}\n\n` +
      `Please help me resolve this issue.`
    );
    window.open(`mailto:support@example.com?subject=${subject}&body=${body}`);
  };
  
  const handleLoadParameters = (parameters: SimulationParameters) => {
    setFormParameters(parameters);
    setCurrentError(null);
    setCurrentResult(null);
    setCurrentStatus(null);
    setIsSimulating(false);
    // Scroll to form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-4 space-y-2 sm:space-y-0">
            <div className="flex items-center">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Physarum 3D Generator</h1>
              <span className="ml-2 sm:ml-3 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                Web Interface
              </span>
            </div>
            <div className="text-sm text-gray-500 sm:text-right">
              Generate 3D models from slime mold simulations
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        {/* Show error display when there's an error */}
        {currentError && (
          <div className="mb-6">
            <ErrorDisplay
              error={currentError}
              onRetry={handleErrorRetry}
              onUsePreset={handleErrorUsePreset}
              onSimplify={handleErrorSimplify}
              onRefresh={handleErrorRefresh}
              onContactSupport={handleErrorContactSupport}
            />
          </div>
        )}
        
        {/* Show parameter form when not simulating and no result */}
        {!isSimulating && !currentResult && !currentError && (
          <ParameterForm
            onSubmit={startSimulation}
            disabled={isSimulating}
            initialValues={formParameters}
            key={JSON.stringify(formParameters)} // Force re-render when parameters change
          />
        )}

        {/* Show simulation status during simulation */}
        {currentStatus && (
          <SimulationStatus
            status={currentStatus}
            onCancel={currentStatus.status === 'running' ? handleCancel : undefined}
          />
        )}

        {/* Show results when simulation is complete */}
        {currentResult && (
          <div className="space-y-6">
            <ResultsDisplay
              result={currentResult}
              onNewSimulation={handleNewSimulation}
            />
            
            {/* Show download history below results */}
            <DownloadHistory
              ref={historyRef}
              onLoadParameters={handleLoadParameters}
              onNewSimulation={handleNewSimulation}
            />
          </div>
        )}
        
        {/* Show download history when not simulating and no current result */}
        {!isSimulating && !currentResult && !currentError && (
          <div className="mt-8">
            <DownloadHistory
              ref={historyRef}
              onLoadParameters={handleLoadParameters}
              onNewSimulation={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            />
          </div>
        )}

        {/* Loading state for initial simulation setup */}
        {isSimulating && !currentStatus && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Preparing simulation...</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-8 sm:mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="text-center text-sm text-gray-500">
            <p className="leading-relaxed">
              Generate 3D printable models from Physarum slime mold simulations. 
              Adjust parameters above to create unique organic structures.
            </p>
            <p className="mt-2 leading-relaxed">
              <span className="font-medium">Tip:</span> Start with a preset for best results, then customize parameters as needed.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;