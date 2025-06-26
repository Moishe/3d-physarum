// ABOUTME: TypeScript interfaces and types for simulation parameters and API responses
// ABOUTME: Defines the structure of all data passed between frontend and backend

export interface SimulationParameters {
  // Simulation Parameters
  width: number;
  height: number;
  actors: number;
  steps: number;
  decay: number;
  viewRadius: number;
  viewDistance: number;
  speed: number;
  speedMin?: number;
  speedMax?: number;
  spawnSpeedRandomization: number;
  initialDiameter: number;
  deathProbability: number;
  spawnProbability: number;
  diffusionRate: number;
  directionDeviation: number;
  image?: string; // Image path for initial actor placement

  // 3D Model Parameters
  smooth: boolean;
  layerHeight: number;
  threshold: number;
  layerFrequency: number;
  smoothingIterations: number;
  smoothingType: 'laplacian' | 'taubin' | 'feature_preserving' | 'boundary_outline';
  taubinLambda: number;
  taubinMu: number;
  preserveFeatures: boolean;
  featureAngle: number;
  meshQuality: boolean;
  background: boolean;
  backgroundDepth: number;
  backgroundMargin: number;
  backgroundBorder: boolean;
  borderHeight: number;
  borderThickness: number;

  // Output Parameters
  output: string;
  quiet: boolean;
  verbose: boolean;
}

export interface SimulationStatus {
  jobId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  currentStep: number;
  totalSteps: number;
  capturedLayers: number;
  actorCount: number;
  trailStats: {
    maxTrail: number;
    meanTrail: number;
  };
  estimatedTimeRemaining?: number;
  progress: number; // 0-100
  error?: string;
}

export interface SimulationResult {
  jobId: string;
  stlPath: string;
  jsonPath: string;
  previewPath: string;
  fileSize: number;
  parameters: SimulationParameters;
  meshMetrics?: {
    vertexCount: number;
    faceCount: number;
    volume: number;
    surfaceArea: number;
    isWatertight: boolean;
    isWindingConsistent: boolean;
    printReady: boolean;
    issues: string[];
  };
  completedAt: string;
}

export interface ParameterPreset {
  name: string;
  description: string;
  parameters: Partial<SimulationParameters>;
}

export const DEFAULT_PARAMETERS: SimulationParameters = {
  // Simulation Parameters
  width: 100,
  height: 100,
  actors: 50,
  steps: 100,
  decay: 0.01,
  viewRadius: 3,
  viewDistance: 10,
  speed: 1.0,
  spawnSpeedRandomization: 0.2,
  initialDiameter: 20.0,
  deathProbability: 0.001,
  spawnProbability: 0.005,
  diffusionRate: 0.0,
  directionDeviation: 1.57,

  // 3D Model Parameters
  smooth: false,
  layerHeight: 1.0,
  threshold: 0.1,
  layerFrequency: 5,
  smoothingIterations: 2,
  smoothingType: 'taubin',
  taubinLambda: 0.5,
  taubinMu: -0.52,
  preserveFeatures: false,
  featureAngle: 60.0,
  meshQuality: false,
  background: false,
  backgroundDepth: 2.0,
  backgroundMargin: 0.05,
  backgroundBorder: false,
  borderHeight: 1.0,
  borderThickness: 0.5,

  // Output Parameters
  output: 'physarum_3d_model.stl',
  quiet: false,
  verbose: false,
};

export const PARAMETER_PRESETS: ParameterPreset[] = [
  {
    name: 'Fast Preview',
    description: 'Quick generation for testing parameters',
    parameters: {
      width: 50,
      height: 50,
      actors: 25,
      steps: 50,
      layerFrequency: 10,
      smooth: false,
    },
  },
  {
    name: 'High Quality',
    description: 'Detailed model with smooth surfaces',
    parameters: {
      width: 200,
      height: 200,
      actors: 100,
      steps: 300,
      smooth: true,
      smoothingIterations: 3,
      layerFrequency: 3,
      meshQuality: true,
    },
  },
  {
    name: 'Complex Structure',
    description: 'Dense network with high actor count',
    parameters: {
      width: 150,
      height: 150,
      actors: 200,
      steps: 400,
      decay: 0.005,
      spawnProbability: 0.01,
      diffusionRate: 0.1,
      smooth: true,
    },
  },
  {
    name: 'Organic Growth',
    description: 'Natural-looking branching patterns',
    parameters: {
      actors: 30,
      steps: 200,
      decay: 0.02,
      viewRadius: 5,
      viewDistance: 15,
      speed: 1.5,
      spawnProbability: 0.003,
      directionDeviation: 0.8,
    },
  },
];