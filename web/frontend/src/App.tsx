// ABOUTME: Main application component that orchestrates the 3D Physarum model generation workflow
// ABOUTME: Manages simulation state and coordinates between parameter form, status display, and results

import { useState } from 'react';
import ParameterForm from './components/ParameterForm';
import SimulationStatus from './components/SimulationStatus';
import ResultsDisplay from './components/ResultsDisplay';
import type { SimulationParameters, SimulationStatus as StatusType, SimulationResult } from './types/simulation';
import './App.css';

function App() {
  const [currentStatus, setCurrentStatus] = useState<StatusType | null>(null);
  const [currentResult, setCurrentResult] = useState<SimulationResult | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Mock function to simulate API call - will be replaced with real API integration
  const startSimulation = async (parameters: SimulationParameters) => {
    const jobId = `sim_${Date.now()}`;
    
    setIsSimulating(true);
    setCurrentResult(null);
    
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

    // Mock simulation progress
    try {
      // Simulate running status
      setTimeout(() => {
        setCurrentStatus(prev => prev ? {
          ...prev,
          status: 'running',
          estimatedTimeRemaining: Math.round(parameters.steps * 0.5), // Mock estimation
        } : null);
      }, 1000);

      // Mock progress updates
      const progressInterval = setInterval(() => {
        setCurrentStatus(prev => {
          if (!prev || prev.status !== 'running') return prev;
          
          const newStep = Math.min(prev.currentStep + Math.floor(Math.random() * 5) + 1, prev.totalSteps);
          const progress = (newStep / prev.totalSteps) * 100;
          const layersCapturing = Math.floor(newStep / parameters.layerFrequency);
          
          return {
            ...prev,
            currentStep: newStep,
            capturedLayers: layersCapturing,
            actorCount: prev.actorCount + Math.floor(Math.random() * 10) - 5, // Simulate actor changes
            trailStats: {
              maxTrail: Math.random() * 1.0,
              meanTrail: Math.random() * 0.5,
            },
            progress,
            estimatedTimeRemaining: Math.max(0, Math.round((prev.totalSteps - newStep) * 0.5)),
          };
        });
      }, 2000);

      // Mock completion after simulation time
      setTimeout(() => {
        clearInterval(progressInterval);
        
        setCurrentStatus(prev => prev ? {
          ...prev,
          status: 'completed',
          currentStep: prev.totalSteps,
          progress: 100,
          estimatedTimeRemaining: 0,
        } : null);

        // Mock result
        const mockResult: SimulationResult = {
          jobId,
          stlPath: `/api/download/${jobId}/model.stl`,
          jsonPath: `/api/download/${jobId}/parameters.json`,
          previewPath: `/api/download/${jobId}/preview.jpg`,
          fileSize: Math.floor(Math.random() * 1024 * 1024 * 5), // Random file size up to 5MB
          parameters,
          meshMetrics: parameters.meshQuality ? {
            vertexCount: Math.floor(Math.random() * 50000) + 10000,
            faceCount: Math.floor(Math.random() * 100000) + 20000,
            volume: Math.random() * 1000 + 100,
            surfaceArea: Math.random() * 5000 + 1000,
            isWatertight: Math.random() > 0.2,
            isWindingConsistent: Math.random() > 0.1,
            printReady: Math.random() > 0.3,
            issues: Math.random() > 0.5 ? [] : ['Minor self-intersections detected', 'Some faces may be too small for printing'],
          } : undefined,
          completedAt: new Date().toISOString(),
        };

        setCurrentResult(mockResult);
        setIsSimulating(false);
      }, parameters.steps * 100); // Mock duration based on steps

    } catch (error) {
      console.error('Simulation error:', error);
      setCurrentStatus(prev => prev ? {
        ...prev,
        status: 'failed',
        error: 'Simulation failed due to an unexpected error',
      } : null);
      setIsSimulating(false);
    }
  };

  const handleCancel = () => {
    setCurrentStatus(prev => prev ? {
      ...prev,
      status: 'cancelled',
    } : null);
    setIsSimulating(false);
  };

  const handleNewSimulation = () => {
    setCurrentStatus(null);
    setCurrentResult(null);
    setIsSimulating(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Physarum 3D Generator</h1>
              <span className="ml-3 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                Web Interface
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Generate 3D models from slime mold simulations
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6">
        {/* Show parameter form when not simulating and no result */}
        {!isSimulating && !currentResult && (
          <ParameterForm
            onSubmit={startSimulation}
            disabled={isSimulating}
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
          <ResultsDisplay
            result={currentResult}
            onNewSimulation={handleNewSimulation}
          />
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
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="text-center text-sm text-gray-500">
            <p>
              Generate 3D printable models from Physarum slime mold simulations. 
              Adjust parameters above to create unique organic structures.
            </p>
            <p className="mt-2">
              <span className="font-medium">Tip:</span> Start with a preset for best results, then customize parameters as needed.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;