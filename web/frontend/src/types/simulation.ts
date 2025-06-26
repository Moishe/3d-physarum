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
  estimatedTime?: string;
  complexity?: 'low' | 'medium' | 'high' | 'very_high';
  tags?: string[];
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

export interface PresetCategory {
  name: string;
  description: string;
  presets: ParameterPreset[];
}

export const PARAMETER_PRESETS: ParameterPreset[] = [
  {
    name: 'Fast Preview',
    description: 'Quick generation for testing parameters (~1-2 min)',
    parameters: {
      width: 50,
      height: 50,
      actors: 25,
      steps: 50,
      layerFrequency: 10,
      smooth: false,
      output: 'fast_preview.stl',
    },
  },
  {
    name: 'Balanced Quality',
    description: 'Good quality with reasonable time (~5-10 min)',
    parameters: {
      width: 100,
      height: 100,
      actors: 75,
      steps: 150,
      smooth: true,
      smoothingIterations: 2,
      layerFrequency: 5,
      meshQuality: false,
      output: 'balanced_quality.stl',
    },
  },
  {
    name: 'High Quality',
    description: 'Detailed model with smooth surfaces (~15-30 min)',
    parameters: {
      width: 200,
      height: 200,
      actors: 100,
      steps: 300,
      smooth: true,
      smoothingIterations: 3,
      layerFrequency: 3,
      meshQuality: true,
      preserveFeatures: true,
      featureAngle: 45,
      output: 'high_quality.stl',
    },
  },
  {
    name: 'Complex Structure',
    description: 'Dense network with intricate patterns (~20-45 min)',
    parameters: {
      width: 150,
      height: 150,
      actors: 200,
      steps: 400,
      decay: 0.005,
      spawnProbability: 0.01,
      diffusionRate: 0.1,
      smooth: true,
      smoothingIterations: 2,
      layerFrequency: 4,
      output: 'complex_structure.stl',
    },
  },
  {
    name: 'Organic Growth',
    description: 'Natural branching patterns (~10-20 min)',
    parameters: {
      width: 120,
      height: 120,
      actors: 30,
      steps: 250,
      decay: 0.02,
      viewRadius: 5,
      viewDistance: 15,
      speed: 1.5,
      spawnProbability: 0.003,
      directionDeviation: 0.8,
      smooth: true,
      smoothingIterations: 2,
      output: 'organic_growth.stl',
    },
  },
  {
    name: 'Printable Model',
    description: 'Optimized for 3D printing with background (~10-15 min)',
    parameters: {
      width: 100,
      height: 100,
      actors: 60,
      steps: 180,
      smooth: true,
      smoothingIterations: 3,
      layerFrequency: 5,
      meshQuality: true,
      background: true,
      backgroundDepth: 2.0,
      backgroundMargin: 0.1,
      backgroundBorder: true,
      borderHeight: 1.5,
      borderThickness: 1.0,
      threshold: 0.15,
      output: 'printable_model.stl',
    },
  },
  {
    name: 'Miniature Detail',
    description: 'Fine details for small models (~5-10 min)',
    parameters: {
      width: 80,
      height: 80,
      actors: 40,
      steps: 120,
      decay: 0.015,
      viewRadius: 2,
      viewDistance: 8,
      speed: 0.8,
      layerHeight: 0.5,
      layerFrequency: 3,
      smooth: true,
      smoothingIterations: 4,
      threshold: 0.2,
      output: 'miniature_detail.stl',
    },
  },
  {
    name: 'Artistic Abstract',
    description: 'Creative patterns with high randomness (~15-25 min)',
    parameters: {
      width: 140,
      height: 140,
      actors: 80,
      steps: 320,
      decay: 0.008,
      spawnProbability: 0.008,
      spawnSpeedRandomization: 0.5,
      directionDeviation: 1.2,
      diffusionRate: 0.05,
      smooth: true,
      smoothingIterations: 2,
      layerFrequency: 4,
      output: 'artistic_abstract.stl',
    },
  },
];

export const PRESET_CATEGORIES: PresetCategory[] = [
  {
    name: 'Quick Start',
    description: 'Fast presets for testing and preview',
    presets: PARAMETER_PRESETS.filter(p => 
      ['Fast Preview', 'Balanced Quality'].includes(p.name)
    ),
  },
  {
    name: 'Quality Focus',
    description: 'High-quality models for final output',
    presets: PARAMETER_PRESETS.filter(p => 
      ['High Quality', 'Printable Model'].includes(p.name)
    ),
  },
  {
    name: 'Creative Patterns',
    description: 'Unique and artistic configurations',
    presets: PARAMETER_PRESETS.filter(p => 
      ['Complex Structure', 'Organic Growth', 'Artistic Abstract'].includes(p.name)
    ),
  },
  {
    name: 'Specialized',
    description: 'Purpose-built configurations',
    presets: PARAMETER_PRESETS.filter(p => 
      ['Miniature Detail'].includes(p.name)
    ),
  },
];