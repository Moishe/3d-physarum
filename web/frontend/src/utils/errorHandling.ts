// ABOUTME: Error handling utilities for user-friendly error messages and recovery suggestions
// ABOUTME: Provides centralized error categorization, formatting, and actionable guidance

export interface ErrorInfo {
  type: 'validation' | 'network' | 'server' | 'timeout' | 'unknown';
  title: string;
  message: string;
  suggestions: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  recoverable: boolean;
  code?: string;
}

export interface NetworkError extends Error {
  status?: number;
  response?: any;
}

export const ERROR_MESSAGES = {
  // Validation errors
  INVALID_PARAMETERS: {
    type: 'validation' as const,
    title: 'Invalid Parameters',
    message: 'Some parameters are invalid or missing.',
    suggestions: [
      'Check the highlighted fields for errors',
      'Use a preset to start with valid parameters',
      'Ensure all required fields are filled'
    ],
    severity: 'medium' as const,
    recoverable: true,
  },
  
  // Network errors
  CONNECTION_FAILED: {
    type: 'network' as const,
    title: 'Connection Failed',
    message: 'Unable to connect to the simulation server.',
    suggestions: [
      'Check your internet connection',
      'Refresh the page and try again',
      'Contact support if the problem persists'
    ],
    severity: 'high' as const,
    recoverable: true,
  },
  
  TIMEOUT: {
    type: 'timeout' as const,
    title: 'Request Timeout',
    message: 'The request took too long to complete.',
    suggestions: [
      'Try reducing simulation complexity',
      'Use a faster preset configuration',
      'Check your network connection'
    ],
    severity: 'medium' as const,
    recoverable: true,
  },
  
  // Server errors
  SERVER_ERROR: {
    type: 'server' as const,
    title: 'Server Error',
    message: 'The simulation server encountered an error.',
    suggestions: [
      'Try again in a few moments',
      'Use a different parameter configuration',
      'Contact support if the error persists'
    ],
    severity: 'high' as const,
    recoverable: true,
  },
  
  SIMULATION_FAILED: {
    type: 'server' as const,
    title: 'Simulation Failed',
    message: 'The simulation could not complete successfully.',
    suggestions: [
      'Check parameter values for extreme configurations',
      'Try a preset configuration',
      'Reduce simulation complexity',
      'Report this issue if it continues'
    ],
    severity: 'high' as const,
    recoverable: true,
  },
  
  INSUFFICIENT_RESOURCES: {
    type: 'server' as const,
    title: 'Insufficient Resources',
    message: 'The server does not have enough resources to complete this simulation.',
    suggestions: [
      'Reduce grid size (width × height)',
      'Decrease the number of actors',
      'Reduce the number of simulation steps',
      'Try again later when the server is less busy'
    ],
    severity: 'medium' as const,
    recoverable: true,
  },
  
  // File/download errors
  FILE_NOT_FOUND: {
    type: 'server' as const,
    title: 'File Not Found',
    message: 'The requested file could not be found.',
    suggestions: [
      'The simulation may have expired',
      'Try generating a new model',
      'Contact support if this persists'
    ],
    severity: 'medium' as const,
    recoverable: true,
  },
  
  DOWNLOAD_FAILED: {
    type: 'network' as const,
    title: 'Download Failed',
    message: 'The file download was interrupted or failed.',
    suggestions: [
      'Try downloading again',
      'Check your internet connection',
      'Try a different browser if the problem persists'
    ],
    severity: 'medium' as const,
    recoverable: true,
  },
  
  // Unknown errors
  UNKNOWN_ERROR: {
    type: 'unknown' as const,
    title: 'Unexpected Error',
    message: 'An unexpected error occurred.',
    suggestions: [
      'Refresh the page and try again',
      'Clear your browser cache',
      'Contact support with error details'
    ],
    severity: 'high' as const,
    recoverable: true,
  },
};

export function categorizeError(error: Error | NetworkError | string): ErrorInfo {
  if (typeof error === 'string') {
    error = new Error(error);
  }
  
  const networkError = error as NetworkError;
  
  // Network-specific errors
  if (networkError.status) {
    switch (networkError.status) {
      case 400:
        return { ...ERROR_MESSAGES.INVALID_PARAMETERS, code: '400' };
      case 404:
        return { ...ERROR_MESSAGES.FILE_NOT_FOUND, code: '404' };
      case 408:
        return { ...ERROR_MESSAGES.TIMEOUT, code: '408' };
      case 413:
        return { 
          ...ERROR_MESSAGES.INSUFFICIENT_RESOURCES, 
          code: '413',
          message: 'Request too large - simulation parameters exceed server limits.',
        };
      case 429:
        return {
          type: 'server',
          title: 'Too Many Requests',
          message: 'You are making requests too quickly.',
          suggestions: [
            'Wait a moment before trying again',
            'Avoid starting multiple simulations simultaneously'
          ],
          severity: 'medium',
          recoverable: true,
          code: '429',
        };
      case 500:
      case 502:
      case 503:
        return { ...ERROR_MESSAGES.SERVER_ERROR, code: networkError.status.toString() };
      default:
        if (networkError.status >= 400 && networkError.status < 500) {
          return { ...ERROR_MESSAGES.INVALID_PARAMETERS, code: networkError.status.toString() };
        } else {
          return { ...ERROR_MESSAGES.SERVER_ERROR, code: networkError.status.toString() };
        }
    }
  }
  
  // Message-based error detection
  const message = error.message.toLowerCase();
  
  if (message.includes('network') || message.includes('connection') || message.includes('fetch')) {
    return ERROR_MESSAGES.CONNECTION_FAILED;
  }
  
  if (message.includes('timeout') || message.includes('timed out')) {
    return ERROR_MESSAGES.TIMEOUT;
  }
  
  if (message.includes('simulation') && message.includes('failed')) {
    return ERROR_MESSAGES.SIMULATION_FAILED;
  }
  
  if (message.includes('validation') || message.includes('invalid')) {
    return ERROR_MESSAGES.INVALID_PARAMETERS;
  }
  
  if (message.includes('file') && message.includes('not found')) {
    return ERROR_MESSAGES.FILE_NOT_FOUND;
  }
  
  if (message.includes('download')) {
    return ERROR_MESSAGES.DOWNLOAD_FAILED;
  }
  
  // Default to unknown error
  return {
    ...ERROR_MESSAGES.UNKNOWN_ERROR,
    message: error.message || 'An unexpected error occurred.',
  };
}

export function formatErrorForUser(error: Error | NetworkError | string): ErrorInfo {
  const errorInfo = categorizeError(error);
  
  // Add contextual information based on error type
  switch (errorInfo.type) {
    case 'validation':
      return {
        ...errorInfo,
        suggestions: [
          ...errorInfo.suggestions,
          'Use the validation indicators to identify issues',
          'Try starting with a preset configuration'
        ]
      };
      
    case 'network':
      return {
        ...errorInfo,
        suggestions: [
          ...errorInfo.suggestions,
          'Ensure you have a stable internet connection',
          'Try disabling browser extensions that might block requests'
        ]
      };
      
    case 'server':
      return {
        ...errorInfo,
        suggestions: [
          ...errorInfo.suggestions,
          'The issue is on our end - we\'re working to fix it',
          'Try a simpler configuration while we resolve this'
        ]
      };
      
    default:
      return errorInfo;
  }
}

export function getRecoveryActions(errorInfo: ErrorInfo): Array<{
  label: string;
  action: 'retry' | 'preset' | 'simplify' | 'contact' | 'refresh';
  primary?: boolean;
}> {
  const actions: Array<{
    label: string;
    action: 'retry' | 'preset' | 'simplify' | 'contact' | 'refresh';
    primary?: boolean;
  }> = [];
  
  switch (errorInfo.type) {
    case 'validation':
      actions.push(
        { label: 'Use Preset', action: 'preset', primary: true },
        { label: 'Try Again', action: 'retry' }
      );
      break;
      
    case 'network':
    case 'timeout':
      actions.push(
        { label: 'Try Again', action: 'retry', primary: true },
        { label: 'Refresh Page', action: 'refresh' }
      );
      break;
      
    case 'server':
      if (errorInfo.code === '413' || errorInfo.title.includes('Resources')) {
        actions.push(
          { label: 'Simplify Parameters', action: 'simplify', primary: true },
          { label: 'Use Fast Preset', action: 'preset' },
          { label: 'Try Again', action: 'retry' }
        );
      } else {
        actions.push(
          { label: 'Try Again', action: 'retry', primary: true },
          { label: 'Use Preset', action: 'preset' }
        );
      }
      break;
      
    default:
      actions.push(
        { label: 'Try Again', action: 'retry', primary: true },
        { label: 'Refresh Page', action: 'refresh' },
        { label: 'Contact Support', action: 'contact' }
      );
  }
  
  // Always offer contact support for high severity errors
  if (errorInfo.severity === 'high' || errorInfo.severity === 'critical') {
    if (!actions.find(a => a.action === 'contact')) {
      actions.push({ label: 'Contact Support', action: 'contact' });
    }
  }
  
  return actions;
}