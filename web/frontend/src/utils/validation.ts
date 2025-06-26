// ABOUTME: Parameter validation utilities using Zod for real-time form validation
// ABOUTME: Provides comprehensive validation schema and error messages for simulation parameters

import { z } from 'zod';
import type { SimulationParameters } from '../types/simulation';

// Custom validation messages
const validationMessages = {
  required: 'This field is required',
  positive: 'Value must be positive',
  nonNegative: 'Value must be non-negative',
  range: (min: number, max: number) => `Value must be between ${min} and ${max}`,
  minValue: (min: number) => `Value must be at least ${min}`,
  maxValue: (max: number) => `Value must be at most ${max}`,
  stlExtension: 'Filename must end with .stl',
  validFilename: 'Filename must be valid (alphanumeric, dashes, underscores)',
};

// Base validation schema without refinements
const baseSimulationParametersSchema = z.object({
  // Simulation Parameters
  width: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Width must be a number',
  }).int().min(10, validationMessages.minValue(10)).max(2000, validationMessages.maxValue(2000)),

  height: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Height must be a number',
  }).int().min(10, validationMessages.minValue(10)).max(2000, validationMessages.maxValue(2000)),

  actors: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Actors must be a number',
  }).int().min(1, validationMessages.minValue(1)).max(10000, validationMessages.maxValue(10000)),

  steps: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Steps must be a number',
  }).int().min(1, validationMessages.minValue(1)).max(100000, validationMessages.maxValue(100000)),

  decay: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Decay must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  viewRadius: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'View radius must be a number',
  }).min(0, validationMessages.nonNegative).max(50, validationMessages.maxValue(50)),

  viewDistance: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'View distance must be a number',
  }).min(0, validationMessages.nonNegative).max(100, validationMessages.maxValue(100)),

  speed: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Speed must be a number',
  }).min(0, validationMessages.nonNegative).max(10, validationMessages.maxValue(10)),

  speedMin: z.number().min(0, validationMessages.nonNegative).max(10, validationMessages.maxValue(10)).optional(),
  speedMax: z.number().min(0, validationMessages.nonNegative).max(10, validationMessages.maxValue(10)).optional(),

  spawnSpeedRandomization: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Spawn speed randomization must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  initialDiameter: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Initial diameter must be a number',
  }).min(1, validationMessages.minValue(1)).max(1000, validationMessages.maxValue(1000)),

  deathProbability: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Death probability must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  spawnProbability: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Spawn probability must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  diffusionRate: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Diffusion rate must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  directionDeviation: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Direction deviation must be a number',
  }).min(0, validationMessages.nonNegative).max(Math.PI, validationMessages.maxValue(Math.PI)),

  image: z.string().optional(),

  // 3D Model Parameters
  smooth: z.boolean(),

  layerHeight: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Layer height must be a number',
  }).min(0.1, validationMessages.minValue(0.1)).max(100, validationMessages.maxValue(100)),

  threshold: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Threshold must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  layerFrequency: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Layer frequency must be a number',
  }).int().min(1, validationMessages.minValue(1)).max(1000, validationMessages.maxValue(1000)),

  smoothingIterations: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Smoothing iterations must be a number',
  }).int().min(0, validationMessages.nonNegative).max(10, validationMessages.maxValue(10)),

  smoothingType: z.enum(['laplacian', 'taubin', 'feature_preserving', 'boundary_outline']),

  taubinLambda: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Taubin lambda must be a number',
  }).min(0.01, validationMessages.minValue(0.01)).max(0.99, validationMessages.maxValue(0.99)),

  taubinMu: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Taubin mu must be a number',
  }).min(-0.99, validationMessages.minValue(-0.99)).max(-0.01, validationMessages.maxValue(-0.01)),

  preserveFeatures: z.boolean(),

  featureAngle: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Feature angle must be a number',
  }).min(1, validationMessages.minValue(1)).max(179, validationMessages.maxValue(179)),

  meshQuality: z.boolean(),
  background: z.boolean(),

  backgroundDepth: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Background depth must be a number',
  }).min(0.1, validationMessages.minValue(0.1)).max(100, validationMessages.maxValue(100)),

  backgroundMargin: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Background margin must be a number',
  }).min(0, validationMessages.nonNegative).max(1, validationMessages.maxValue(1)),

  backgroundBorder: z.boolean(),

  borderHeight: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Border height must be a number',
  }).min(0.1, validationMessages.minValue(0.1)).max(100, validationMessages.maxValue(100)),

  borderThickness: z.number({
    required_error: validationMessages.required,
    invalid_type_error: 'Border thickness must be a number',
  }).min(0.1, validationMessages.minValue(0.1)).max(100, validationMessages.maxValue(100)),

  // Output Parameters
  output: z.string({
    required_error: validationMessages.required,
  }).min(1, 'Filename cannot be empty')
    .regex(/\.stl$/, validationMessages.stlExtension)
    .regex(/^[a-zA-Z0-9_\-\.]+$/, validationMessages.validFilename),

  quiet: z.boolean(),
  verbose: z.boolean(),
});

// Export the refined schema for full validation
export const simulationParametersSchema = baseSimulationParametersSchema.refine((data) => {
  // Custom validation: speedMin must be less than speedMax if both are provided
  if (data.speedMin !== undefined && data.speedMax !== undefined) {
    return data.speedMin <= data.speedMax;
  }
  return true;
}, {
  message: 'Speed minimum must be less than or equal to speed maximum',
  path: ['speedMin'],
}).refine((data) => {
  // Custom validation: simulation area should not be too large for performance
  const totalCells = data.width * data.height;
  const maxCells = 500000; // 500k cells max for reasonable performance
  return totalCells <= maxCells;
}, {
  message: `Simulation area too large (${500000} cells max). Consider reducing width or height.`,
  path: ['width'],
}).refine((data) => {
  // Custom validation: warn about high step counts with many actors
  const complexity = data.steps * data.actors;
  const maxComplexity = 2000000; // 2M for reasonable simulation time
  return complexity <= maxComplexity;
}, {
  message: 'High complexity simulation may take very long. Consider reducing steps or actors.',
  path: ['steps'],
});

// Individual field validation functions
export const validateField = (field: keyof SimulationParameters, value: any): string | null => {
  try {
    const fieldSchema = baseSimulationParametersSchema.shape[field];
    if (fieldSchema) {
      fieldSchema.parse(value);
    }
    return null;
  } catch (error) {
    if (error instanceof z.ZodError) {
      return error.errors[0]?.message || 'Invalid value';
    }
    return 'Invalid value';
  }
};

// Full form validation
export const validateParameters = (parameters: SimulationParameters): { 
  isValid: boolean; 
  errors: Record<string, string>;
  warnings: Record<string, string>; 
} => {
  const result = simulationParametersSchema.safeParse(parameters);
  
  if (result.success) {
    return { isValid: true, errors: {}, warnings: {} };
  }

  const errors: Record<string, string> = {};
  const warnings: Record<string, string> = {};

  result.error.errors.forEach((error) => {
    const field = error.path[0] as string;
    const message = error.message;
    
    // Classify warnings vs errors
    if (message.toLowerCase().includes('may take very long') || 
        message.toLowerCase().includes('high complexity')) {
      warnings[field] = message;
    } else {
      errors[field] = message;
    }
  });

  return { 
    isValid: Object.keys(errors).length === 0, 
    errors, 
    warnings 
  };
};

// Performance estimation helper
export const estimateSimulationTime = (parameters: SimulationParameters): {
  estimatedSeconds: number;
  complexity: 'low' | 'medium' | 'high' | 'very_high';
  warnings: string[];
} => {
  const { width, height, actors, steps } = parameters;
  const totalCells = width * height;
  const totalOperations = totalCells * actors * steps;
  
  // Rough estimation based on typical performance
  // These are very rough estimates and will vary greatly by hardware
  const baseTimePerOperation = 0.000001; // 1 microsecond per operation
  const estimatedSeconds = totalOperations * baseTimePerOperation;
  
  let complexity: 'low' | 'medium' | 'high' | 'very_high';
  const warnings: string[] = [];
  
  if (estimatedSeconds < 30) {
    complexity = 'low';
  } else if (estimatedSeconds < 300) { // 5 minutes
    complexity = 'medium';
  } else if (estimatedSeconds < 1800) { // 30 minutes
    complexity = 'high';
    warnings.push('This simulation may take 5-30 minutes to complete');
  } else {
    complexity = 'very_high';
    warnings.push('This simulation may take over 30 minutes to complete');
    warnings.push('Consider reducing grid size, actors, or steps for faster results');
  }
  
  // Additional warnings based on specific parameters
  if (totalCells > 200000) {
    warnings.push('Large grid size may require significant memory');
  }
  
  if (actors > 500) {
    warnings.push('High actor count may slow down simulation significantly');
  }
  
  if (steps > 1000) {
    warnings.push('Many simulation steps will increase generation time');
  }
  
  return {
    estimatedSeconds,
    complexity,
    warnings,
  };
};