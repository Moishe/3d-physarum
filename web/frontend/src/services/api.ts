// ABOUTME: API service module for communicating with the FastAPI backend
// ABOUTME: Handles all HTTP requests for simulation management and file downloads

import type { SimulationParameters, SimulationStatus, SimulationResult } from '../types/simulation';

// Model registry types
interface ModelRecord {
  id: string;
  created_at: number;
  name: string;
  stl_path?: string;
  json_path?: string;
  jpg_path?: string;
  parameters: Record<string, any>;
  source: 'cli' | 'web' | 'unknown';
  git_commit?: string;
  file_sizes: Record<string, number>;
  favorite: boolean;
  tags: string[];
}

interface ModelListResponse {
  success: boolean;
  data: {
    models: ModelRecord[];
    total_count: number;
    returned_count: number;
    offset: number;
    has_more: boolean;
  };
  statistics: Record<string, any>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API response types that match the backend
interface ApiSimulationResponse {
  job_id: string;
  status: string;
  message: string;
}

interface ApiStatusResponse {
  job_id: string;
  status: string;
  progress?: {
    job_id: string;
    step: number;
    total_steps: number;
    layers_captured: number;
    actor_count: number;
    max_trail: number;
    mean_trail: number;
    estimated_completion_time?: number;
    timestamp: number;
  };
  error_message?: string;
  started_at?: number;
  completed_at?: number;
}

interface ApiResultResponse {
  job_id: string;
  status: string;
  parameters: any;
  files: Record<string, string>;
  statistics: Record<string, any>;
  mesh_quality?: {
    vertex_count: number;
    face_count: number;
    volume: number;
    surface_area: number;
    is_watertight: boolean;
    is_winding_consistent: boolean;
    print_ready: boolean;
    issues: string[];
  };
  completed_at: number;
  file_sizes: Record<string, number>;
}

class ApiError extends Error {
  public status: number;
  public details?: any;

  constructor(
    message: string,
    status: number,
    details?: any
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

// Convert frontend parameters to backend format
function convertParametersToBackend(params: SimulationParameters): any {
  return {
    width: params.width,
    height: params.height,
    actors: params.actors,
    steps: params.steps,
    decay: params.decay,
    view_radius: params.viewRadius,
    view_distance: params.viewDistance,
    speed: params.speed,
    speed_min: params.speedMin,
    speed_max: params.speedMax,
    spawn_speed_randomization: params.spawnSpeedRandomization,
    initial_diameter: params.initialDiameter,
    death_probability: params.deathProbability,
    spawn_probability: params.spawnProbability,
    diffusion_rate: params.diffusionRate,
    direction_deviation: params.directionDeviation,
    image: params.image,
    smooth: params.smooth,
    layer_height: params.layerHeight,
    threshold: params.threshold,
    layer_frequency: params.layerFrequency,
    smoothing_iterations: params.smoothingIterations,
    smoothing_type: params.smoothingType,
    taubin_lambda: params.taubinLambda,
    taubin_mu: params.taubinMu,
    preserve_features: params.preserveFeatures,
    feature_angle: params.featureAngle,
    mesh_quality: params.meshQuality,
    background: params.background,
    background_depth: params.backgroundDepth,
    background_margin: params.backgroundMargin,
    background_border: params.backgroundBorder,
    border_height: params.borderHeight,
    border_thickness: params.borderThickness,
    output: params.output,
  };
}

// Convert backend status to frontend format
function convertStatusToFrontend(apiStatus: ApiStatusResponse): SimulationStatus {
  const status: SimulationStatus = {
    jobId: apiStatus.job_id,
    status: apiStatus.status as any,
    currentStep: apiStatus.progress?.step || 0,
    totalSteps: apiStatus.progress?.total_steps || 0,
    capturedLayers: apiStatus.progress?.layers_captured || 0,
    actorCount: apiStatus.progress?.actor_count || 0,
    trailStats: {
      maxTrail: apiStatus.progress?.max_trail || 0,
      meanTrail: apiStatus.progress?.mean_trail || 0,
    },
    progress: apiStatus.progress 
      ? (apiStatus.progress.step / apiStatus.progress.total_steps) * 100 
      : 0,
  };

  if (apiStatus.progress?.estimated_completion_time) {
    status.estimatedTimeRemaining = apiStatus.progress.estimated_completion_time;
  }

  if (apiStatus.error_message) {
    status.error = apiStatus.error_message;
  }

  return status;
}

// Convert backend result to frontend format
function convertResultToFrontend(apiResult: ApiResultResponse): SimulationResult {
  return {
    jobId: apiResult.job_id,
    stlPath: `/api/simulate/${apiResult.job_id}/download/stl`,
    jsonPath: `/api/simulate/${apiResult.job_id}/download/json`,
    previewPath: `/api/simulate/${apiResult.job_id}/download/preview`,
    fileSize: apiResult.file_sizes.stl || 0,
    parameters: apiResult.parameters,
    meshMetrics: apiResult.mesh_quality ? {
      vertexCount: apiResult.mesh_quality.vertex_count,
      faceCount: apiResult.mesh_quality.face_count,
      volume: apiResult.mesh_quality.volume,
      surfaceArea: apiResult.mesh_quality.surface_area,
      isWatertight: apiResult.mesh_quality.is_watertight,
      isWindingConsistent: apiResult.mesh_quality.is_winding_consistent,
      printReady: apiResult.mesh_quality.print_ready,
      issues: apiResult.mesh_quality.issues,
    } : undefined,
    completedAt: new Date(apiResult.completed_at * 1000).toISOString(),
  };
}

async function makeRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    let errorDetails;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.message || errorData.error || errorMessage;
      errorDetails = errorData.details || errorData;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    
    throw new ApiError(errorMessage, response.status, errorDetails);
  }

  return response.json();
}

export const api = {
  // Start a new simulation
  async startSimulation(parameters: SimulationParameters): Promise<{ jobId: string; message: string }> {
    const backendParams = convertParametersToBackend(parameters);
    
    const response = await makeRequest<ApiSimulationResponse>('/api/simulate', {
      method: 'POST',
      body: JSON.stringify({ parameters: backendParams }),
    });

    return {
      jobId: response.job_id,
      message: response.message,
    };
  },

  // Get simulation status
  async getSimulationStatus(jobId: string): Promise<SimulationStatus> {
    const response = await makeRequest<ApiStatusResponse>(`/api/simulate/${jobId}/status`);
    return convertStatusToFrontend(response);
  },

  // Get simulation result
  async getSimulationResult(jobId: string): Promise<SimulationResult> {
    const response = await makeRequest<ApiResultResponse>(`/api/simulate/${jobId}/result`);
    return convertResultToFrontend(response);
  },

  // Cancel simulation
  async cancelSimulation(jobId: string): Promise<void> {
    await makeRequest(`/api/simulate/${jobId}`, {
      method: 'DELETE',
    });
  },

  // Get preview image URL
  getPreviewUrl(jobId: string): string {
    return `${API_BASE_URL}/api/simulate/${jobId}/preview`;
  },

  // Get download URL for a file
  getDownloadUrl(jobId: string, fileType: 'stl' | 'json' | 'preview'): string {
    return `${API_BASE_URL}/api/simulate/${jobId}/download/${fileType}`;
  },

  // Model registry API functions
  
  // List models with optional filtering
  async listModels(options?: {
    source?: 'cli' | 'web';
    favorites?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<ModelListResponse> {
    const params = new URLSearchParams();
    
    if (options?.source) params.append('source', options.source);
    if (options?.favorites) params.append('favorites', 'true');
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());
    
    const endpoint = `/api/models/?${params.toString()}`;
    return await makeRequest<ModelListResponse>(endpoint);
  },

  // Get specific model details
  async getModel(modelId: string): Promise<{ success: boolean; data: ModelRecord }> {
    return await makeRequest<{ success: boolean; data: ModelRecord }>(`/api/models/${modelId}`);
  },

  // Update model metadata
  async updateModel(modelId: string, updates: {
    name?: string;
    favorite?: boolean;
    tags?: string[];
  }): Promise<{ success: boolean; message: string }> {
    return await makeRequest<{ success: boolean; message: string }>(`/api/models/${modelId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  },

  // Delete model
  async deleteModel(modelId: string, deleteFiles = false): Promise<{ success: boolean; message: string }> {
    const params = deleteFiles ? '?delete_files=true' : '';
    return await makeRequest<{ success: boolean; message: string }>(`/api/models/${modelId}${params}`, {
      method: 'DELETE',
    });
  },

  // Trigger model scan
  async scanModels(): Promise<{ success: boolean; message: string }> {
    return await makeRequest<{ success: boolean; message: string }>('/api/models/scan', {
      method: 'POST',
    });
  },

  // Get model statistics
  async getModelStatistics(): Promise<{ success: boolean; data: Record<string, any> }> {
    return await makeRequest<{ success: boolean; data: Record<string, any> }>('/api/models/statistics');
  },

  // Get model download URL
  getModelDownloadUrl(modelId: string, fileType: 'stl' | 'json' | 'jpg' | 'preview'): string {
    return `${API_BASE_URL}/api/models/${modelId}/download/${fileType}`;
  },
};

export { ApiError };
export type { ModelRecord, ModelListResponse };