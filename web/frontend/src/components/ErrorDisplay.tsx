// ABOUTME: Reusable error display component with user-friendly messages and recovery actions
// ABOUTME: Provides consistent error presentation with severity-based styling and actionable suggestions

// No React imports needed for functional components in React 19
import { formatErrorForUser, getRecoveryActions, type ErrorInfo } from '../utils/errorHandling';

interface ErrorDisplayProps {
  error: Error | string | ErrorInfo;
  onRetry?: () => void;
  onUsePreset?: () => void;
  onSimplify?: () => void;
  onRefresh?: () => void;
  onContactSupport?: () => void;
  className?: string;
  compact?: boolean;
}

export default function ErrorDisplay({ 
  error, 
  onRetry, 
  onUsePreset, 
  onSimplify, 
  onRefresh, 
  onContactSupport,
  className = '',
  compact = false 
}: ErrorDisplayProps) {
  const errorInfo: ErrorInfo = error instanceof Error || typeof error === 'string' 
    ? formatErrorForUser(error) 
    : error;
    
  const recoveryActions = getRecoveryActions(errorInfo);
  
  const handleAction = (actionType: string) => {
    switch (actionType) {
      case 'retry':
        onRetry?.();
        break;
      case 'preset':
        onUsePreset?.();
        break;
      case 'simplify':
        onSimplify?.();
        break;
      case 'refresh':
        onRefresh?.();
        break;
      case 'contact':
        onContactSupport?.();
        break;
    }
  };
  
  const getSeverityStyles = (severity: ErrorInfo['severity']) => {
    switch (severity) {
      case 'low':
        return {
          container: 'bg-blue-50 border-blue-200',
          icon: 'text-blue-400',
          title: 'text-blue-800',
          message: 'text-blue-700',
          iconPath: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z'
        };
      case 'medium':
        return {
          container: 'bg-yellow-50 border-yellow-200',
          icon: 'text-yellow-400',
          title: 'text-yellow-800',
          message: 'text-yellow-700',
          iconPath: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z'
        };
      case 'high':
        return {
          container: 'bg-red-50 border-red-200',
          icon: 'text-red-400',
          title: 'text-red-800',
          message: 'text-red-700',
          iconPath: 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z'
        };
      case 'critical':
        return {
          container: 'bg-red-100 border-red-300',
          icon: 'text-red-500',
          title: 'text-red-900',
          message: 'text-red-800',
          iconPath: 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z'
        };
      default:
        return {
          container: 'bg-gray-50 border-gray-200',
          icon: 'text-gray-400',
          title: 'text-gray-800',
          message: 'text-gray-700',
          iconPath: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z'
        };
    }
  };
  
  const styles = getSeverityStyles(errorInfo.severity);
  
  if (compact) {
    return (
      <div className={`rounded-md border p-3 ${styles.container} ${className}`}>
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className={`h-4 w-4 ${styles.icon}`} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d={styles.iconPath} clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-2 flex-1">
            <h4 className={`text-sm font-medium ${styles.title}`}>
              {errorInfo.title}
            </h4>
            <p className={`text-sm mt-1 ${styles.message}`}>
              {errorInfo.message}
            </p>
            {recoveryActions.length > 0 && (
              <div className="mt-2 flex space-x-2">
                {recoveryActions.slice(0, 2).map((action, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleAction(action.action)}
                    className={`text-xs px-2 py-1 rounded border transition-colors ${
                      action.primary 
                        ? 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50' 
                        : 'bg-transparent border-transparent text-gray-600 hover:bg-white hover:border-gray-300'
                    }`}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`rounded-lg border p-4 ${styles.container} ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className={`h-5 w-5 ${styles.icon}`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d={styles.iconPath} clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className={`text-sm font-medium ${styles.title}`}>
            {errorInfo.title}
            {errorInfo.code && (
              <span className="ml-2 text-xs opacity-75">(Code: {errorInfo.code})</span>
            )}
          </h3>
          
          <div className={`mt-2 text-sm ${styles.message}`}>
            <p>{errorInfo.message}</p>
          </div>
          
          {errorInfo.suggestions.length > 0 && (
            <div className="mt-3">
              <p className={`text-sm font-medium ${styles.title} mb-2`}>What you can do:</p>
              <ul className={`text-sm ${styles.message} space-y-1`}>
                {errorInfo.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-gray-400 mr-2">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {recoveryActions.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {recoveryActions.map((action, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleAction(action.action)}
                  className={`px-3 py-2 text-sm font-medium rounded-md border transition-colors ${
                    action.primary
                      ? 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 shadow-sm'
                      : 'bg-transparent border-gray-200 text-gray-600 hover:bg-white hover:border-gray-300'
                  }`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
          
          {errorInfo.type === 'unknown' && (
            <details className="mt-4">
              <summary className={`text-sm cursor-pointer ${styles.title} opacity-75 hover:opacity-100`}>
                Technical Details
              </summary>
              <div className="mt-2 p-2 bg-gray-100 rounded text-xs font-mono text-gray-600 overflow-auto">
                {error instanceof Error ? error.stack || error.message : JSON.stringify(error, null, 2)}
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}