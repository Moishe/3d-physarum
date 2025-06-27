// ABOUTME: Main form component for simulation parameters organized in collapsible sections
// ABOUTME: Handles form validation, presets, and parameter submission to the simulation API

import { useState, useCallback, useMemo, useEffect } from 'react';
import type { SimulationParameters, ParameterPreset } from '../types/simulation';
import { DEFAULT_PARAMETERS, PRESET_CATEGORIES } from '../types/simulation';
import { validateField, validateParameters, estimateSimulationTime } from '../utils/validation';

interface ParameterFormProps {
  onSubmit: (parameters: SimulationParameters) => void;
  disabled?: boolean;
  initialValues?: Partial<SimulationParameters>;
}

export default function ParameterForm({ onSubmit, disabled = false, initialValues = {} }: ParameterFormProps) {
  const [parameters, setParameters] = useState<SimulationParameters>({
    ...DEFAULT_PARAMETERS,
    ...initialValues,
  });
  
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [fieldWarnings, setFieldWarnings] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  
  // Update parameters when initialValues change (e.g., from loading history)
  useEffect(() => {
    if (Object.keys(initialValues).length > 0) {
      setParameters(prev => ({ ...prev, ...initialValues }));
    }
  }, [initialValues]);
  
  // Performance estimation
  const performanceEstimate = useMemo(() => {
    return estimateSimulationTime(parameters);
  }, [parameters]);

  const [expandedSections, setExpandedSections] = useState({
    simulation: true,
    model3d: false,
    output: false,
    advanced: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all parameters before submission
    const validation = validateParameters(parameters);
    
    if (validation.isValid) {
      onSubmit(parameters);
    } else {
      // Mark all fields as touched to show validation errors
      const newTouched: Record<string, boolean> = {};
      Object.keys(validation.errors).forEach(field => {
        newTouched[field] = true;
      });
      setTouched(prev => ({ ...prev, ...newTouched }));
      setFieldErrors(validation.errors);
      setFieldWarnings(validation.warnings);
    }
  };

  const updateParameter = useCallback((key: keyof SimulationParameters, value: SimulationParameters[keyof SimulationParameters]) => {
    // Batch all state updates to prevent multiple re-renders
    setParameters(prev => {
      const newParams = { ...prev, [key]: value };
      
      // Validate individual field
      const error = validateField(key, value);
      
      // Update touched state
      setTouched(prevTouched => ({ ...prevTouched, [key]: true }));
      
      // Update field errors
      setFieldErrors(prevErrors => {
        const newErrors = { ...prevErrors };
        if (error) {
          newErrors[key] = error;
        } else {
          delete newErrors[key];
        }
        return newErrors;
      });
      
      // Re-validate entire form for cross-field validation (synchronously)
      const validation = validateParameters(newParams);
      setFieldWarnings(validation.warnings);
      
      return newParams;
    });
  }, []);

  const applyPreset = useCallback((preset: ParameterPreset) => {
    const newParams = { ...parameters, ...preset.parameters };
    setParameters(newParams);
    
    // Clear previous validation errors since preset should be valid
    setFieldErrors({});
    setFieldWarnings({});
    setTouched({});
    
    // Re-validate with new parameters
    setTimeout(() => {
      const validation = validateParameters(newParams);
      setFieldWarnings(validation.warnings);
    }, 0);
  }, [parameters]);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const SectionHeader = ({ title, section, children }: { 
    title: string; 
    section: keyof typeof expandedSections;
    children: React.ReactNode;
  }) => (
    <div className="border border-gray-200 rounded-lg mb-4">
      <button
        type="button"
        onClick={() => toggleSection(section)}
        className="w-full px-4 py-3 text-left font-medium text-gray-900 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-t-lg flex justify-between items-center"
      >
        {title}
        <span className={`transform transition-transform ${expandedSections[section] ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {expandedSections[section] && (
        <div className="p-4 space-y-4">
          {children}
        </div>
      )}
    </div>
  );

  const InputField = ({ 
    label, 
    type = 'number', 
    value, 
    onChange, 
    min, 
    max, 
    step,
    help,
    fieldKey 
  }: {
    label: string;
    type?: string;
    value: string | number;
    onChange: (value: string | number) => void;
    min?: number;
    max?: number;
    step?: number;
    help?: string;
    fieldKey?: keyof SimulationParameters;
  }) => {
    const hasError = fieldKey && touched[fieldKey] && fieldErrors[fieldKey];
    const hasWarning = fieldKey && fieldWarnings[fieldKey];
    const borderColor = hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 
                       hasWarning ? 'border-yellow-300 focus:border-yellow-500 focus:ring-yellow-500' :
                       'border-gray-300 focus:border-blue-500 focus:ring-blue-500';
    
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {hasError && <span className="text-red-500 ml-1">*</span>}
          {hasWarning && <span className="text-yellow-500 ml-1">⚠</span>}
        </label>
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none disabled:opacity-50 ${borderColor}`}
        />
        {hasError && (
          <p className="text-xs text-red-600 mt-1 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {fieldErrors[fieldKey!]}
          </p>
        )}
        {hasWarning && !hasError && (
          <p className="text-xs text-yellow-600 mt-1 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {fieldWarnings[fieldKey!]}
          </p>
        )}
        {help && !hasError && !hasWarning && <p className="text-xs text-gray-500 mt-1">{help}</p>}
      </div>
    );
  };

  const CheckboxField = ({ 
    label, 
    checked, 
    onChange, 
    help,
    fieldKey 
  }: {
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    help?: string;
    fieldKey?: keyof SimulationParameters;
  }) => {
    const hasError = fieldKey && touched[fieldKey] && fieldErrors[fieldKey];
    const hasWarning = fieldKey && fieldWarnings[fieldKey];
    
    return (
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
          />
          <span className="ml-2 text-sm font-medium text-gray-700">
            {label}
            {hasError && <span className="text-red-500 ml-1">*</span>}
            {hasWarning && <span className="text-yellow-500 ml-1">⚠</span>}
          </span>
        </label>
        {hasError && (
          <p className="text-xs text-red-600 mt-1 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {fieldErrors[fieldKey!]}
          </p>
        )}
        {hasWarning && !hasError && (
          <p className="text-xs text-yellow-600 mt-1 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {fieldWarnings[fieldKey!]}
          </p>
        )}
        {help && !hasError && !hasWarning && <p className="text-xs text-gray-500 mt-1">{help}</p>}
      </div>
    );
  };

  const SelectField = ({ 
    label, 
    value, 
    options, 
    onChange, 
    help,
    fieldKey 
  }: {
    label: string;
    value: string;
    options: { value: string; label: string }[];
    onChange: (value: string) => void;
    help?: string;
    fieldKey?: keyof SimulationParameters;
  }) => {
    const hasError = fieldKey && touched[fieldKey] && fieldErrors[fieldKey];
    const hasWarning = fieldKey && fieldWarnings[fieldKey];
    const borderColor = hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 
                       hasWarning ? 'border-yellow-300 focus:border-yellow-500 focus:ring-yellow-500' :
                       'border-gray-300 focus:border-blue-500 focus:ring-blue-500';
    
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {hasError && <span className="text-red-500 ml-1">*</span>}
          {hasWarning && <span className="text-yellow-500 ml-1">⚠</span>}
        </label>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none disabled:opacity-50 ${borderColor}`}
        >
          {options.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {hasError && (
          <p className="text-xs text-red-600 mt-1 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {fieldErrors[fieldKey!]}
          </p>
        )}
        {hasWarning && !hasError && (
          <p className="text-xs text-yellow-600 mt-1 flex items-center">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {fieldWarnings[fieldKey!]}
          </p>
        )}
        {help && !hasError && !hasWarning && <p className="text-xs text-gray-500 mt-1">{help}</p>}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Physarum 3D Model Parameters</h2>
        <p className="text-gray-600">Configure simulation parameters to generate your 3D model</p>
        
        {/* Performance Estimation */}
        {performanceEstimate.complexity !== 'low' && (
          <div className={`mt-4 p-4 rounded-lg border ${
            performanceEstimate.complexity === 'very_high' ? 'bg-red-50 border-red-200' :
            performanceEstimate.complexity === 'high' ? 'bg-yellow-50 border-yellow-200' :
            'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {performanceEstimate.complexity === 'very_high' ? (
                  <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 011-1h.01a1 1 0 110 2H12a1 1 0 01-1-1zm.01 4a1 1 0 112 0V14a1 1 0 11-2 0v-4z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${
                  performanceEstimate.complexity === 'very_high' ? 'text-red-800' :
                  performanceEstimate.complexity === 'high' ? 'text-yellow-800' :
                  'text-blue-800'
                }`}>
                  {performanceEstimate.complexity === 'very_high' ? 'Very High Complexity' :
                   performanceEstimate.complexity === 'high' ? 'High Complexity' :
                   'Medium Complexity'} Simulation
                </h3>
                <div className={`mt-2 text-sm ${
                  performanceEstimate.complexity === 'very_high' ? 'text-red-700' :
                  performanceEstimate.complexity === 'high' ? 'text-yellow-700' :
                  'text-blue-700'
                }`}>
                  <p>Estimated time: {Math.round(performanceEstimate.estimatedSeconds / 60)} minutes</p>
                  {performanceEstimate.warnings.map((warning, index) => (
                    <p key={index} className="mt-1">{warning}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Parameter Presets */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Parameter Presets</h3>
        <p className="text-sm text-gray-600 mb-4">
          Choose a preset to quickly configure parameters for different use cases. You can further customize after selecting.
        </p>
        
        <div className="space-y-6">
          {PRESET_CATEGORIES.map(category => (
            <div key={category.name}>
              <div className="mb-3">
                <h4 className="text-md font-medium text-gray-800">{category.name}</h4>
                <p className="text-sm text-gray-500">{category.description}</p>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {category.presets.map(preset => {
                  const estimate = estimateSimulationTime({
                    ...DEFAULT_PARAMETERS,
                    ...preset.parameters
                  } as SimulationParameters);
                  
                  return (
                    <button
                      key={preset.name}
                      type="button"
                      onClick={() => applyPreset(preset)}
                      disabled={disabled}
                      className="group p-4 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-300 disabled:opacity-50 transition-all duration-200"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="font-medium text-gray-900 group-hover:text-blue-900">
                          {preset.name}
                        </div>
                        <div className={`px-2 py-1 text-xs rounded-full ${
                          estimate.complexity === 'low' ? 'bg-green-100 text-green-700' :
                          estimate.complexity === 'medium' ? 'bg-blue-100 text-blue-700' :
                          estimate.complexity === 'high' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {estimate.complexity === 'low' ? 'Fast' :
                           estimate.complexity === 'medium' ? 'Medium' :
                           estimate.complexity === 'high' ? 'Slow' : 'Very Slow'}
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-600 mb-3">
                        {preset.description}
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center space-x-2 sm:space-x-3 text-xs">
                          <span className="truncate">{preset.parameters.width || DEFAULT_PARAMETERS.width}×{preset.parameters.height || DEFAULT_PARAMETERS.height}</span>
                          <span className="truncate">{preset.parameters.actors || DEFAULT_PARAMETERS.actors} actors</span>
                          <span className="truncate hidden sm:inline">{preset.parameters.steps || DEFAULT_PARAMETERS.steps} steps</span>
                        </div>
                        <div className="flex items-center">
                          <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.414-1.414L11 9.586V6z" clipRule="evenodd" />
                          </svg>
                          ~{Math.round(estimate.estimatedSeconds / 60)}min
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
        
        {/* Custom Configuration Notice */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-gray-400 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-sm font-medium text-gray-900">Custom Configuration</p>
              <p className="text-sm text-gray-600 mt-1">
                You can also start with default parameters and customize them manually in the sections below.
                All parameters include validation and performance estimates.
              </p>
            </div>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Simulation Parameters */}
        <SectionHeader title="Simulation Parameters" section="simulation">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <InputField
              label="Width"
              value={parameters.width}
              onChange={(value) => updateParameter('width', value)}
              min={10}
              help="Grid width in pixels"
              fieldKey="width"
            />
            <InputField
              label="Height"
              value={parameters.height}
              onChange={(value) => updateParameter('height', value)}
              min={10}
              help="Grid height in pixels"
              fieldKey="height"
            />
            <InputField
              label="Actors"
              value={parameters.actors}
              onChange={(value) => updateParameter('actors', value)}
              min={1}
              help="Number of Physarum actors"
              fieldKey="actors"
            />
            <InputField
              label="Steps"
              value={parameters.steps}
              onChange={(value) => updateParameter('steps', value)}
              min={1}
              help="Number of simulation steps"
              fieldKey="steps"
            />
            <InputField
              label="Decay Rate"
              value={parameters.decay}
              onChange={(value) => updateParameter('decay', value)}
              min={0}
              max={1}
              step={0.001}
              help="Trail decay rate (0.0-1.0)"
              fieldKey="decay"
            />
            <InputField
              label="View Radius"
              value={parameters.viewRadius}
              onChange={(value) => updateParameter('viewRadius', value)}
              min={0}
              help="Actor sensing radius"
              fieldKey="viewRadius"
            />
            <InputField
              label="View Distance"
              value={parameters.viewDistance}
              onChange={(value) => updateParameter('viewDistance', value)}
              min={0}
              help="Actor sensing distance"
              fieldKey="viewDistance"
            />
            <InputField
              label="Speed"
              value={parameters.speed}
              onChange={(value) => updateParameter('speed', value)}
              min={0}
              step={0.1}
              help="Actor movement speed"
              fieldKey="speed"
            />
            <InputField
              label="Diffusion Rate"
              value={parameters.diffusionRate}
              onChange={(value) => updateParameter('diffusionRate', value)}
              min={0}
              max={1}
              step={0.01}
              help="Pheromone diffusion rate"
              fieldKey="diffusionRate"
            />
          </div>
        </SectionHeader>

        {/* 3D Model Parameters */}
        <SectionHeader title="3D Model Parameters" section="model3d">
          <div className="space-y-4">
            <CheckboxField
              label="Use Smooth Surfaces (Marching Cubes)"
              checked={parameters.smooth}
              onChange={(value) => updateParameter('smooth', value)}
              help="Generate smooth surfaces instead of voxel-based models"
              fieldKey="smooth"
            />
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <InputField
                label="Layer Height"
                value={parameters.layerHeight}
                onChange={(value) => updateParameter('layerHeight', value)}
                min={0.1}
                step={0.1}
                help="Height of each layer in 3D model"
                fieldKey="layerHeight"
              />
              <InputField
                label="Threshold"
                value={parameters.threshold}
                onChange={(value) => updateParameter('threshold', value)}
                min={0}
                max={1}
                step={0.01}
                help="Minimum trail strength for 3D inclusion"
                fieldKey="threshold"
              />
              <InputField
                label="Layer Frequency"
                value={parameters.layerFrequency}
                onChange={(value) => updateParameter('layerFrequency', value)}
                min={1}
                help="Capture layer every N steps"
                fieldKey="layerFrequency"
              />
            </div>

            {parameters.smooth && (
              <div className="border-t pt-4 space-y-4">
                <h4 className="font-medium text-gray-900">Smoothing Options</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <InputField
                    label="Smoothing Iterations"
                    value={parameters.smoothingIterations}
                    onChange={(value) => updateParameter('smoothingIterations', value)}
                    min={0}
                    help="Number of smoothing iterations"
                  />
                  <SelectField
                    label="Smoothing Type"
                    value={parameters.smoothingType}
                    options={[
                      { value: 'laplacian', label: 'Laplacian' },
                      { value: 'taubin', label: 'Taubin' },
                      { value: 'feature_preserving', label: 'Feature Preserving' },
                      { value: 'boundary_outline', label: 'Boundary Outline' }
                    ]}
                    onChange={(value) => updateParameter('smoothingType', value as 'laplacian' | 'taubin' | 'feature_preserving' | 'boundary_outline')}
                    help="Type of smoothing algorithm"
                  />
                  {parameters.smoothingType === 'taubin' && (
                    <>
                      <InputField
                        label="Taubin Lambda"
                        value={parameters.taubinLambda}
                        onChange={(value) => updateParameter('taubinLambda', value)}
                        min={0.01}
                        max={0.99}
                        step={0.01}
                        help="Taubin smoothing lambda parameter"
                      />
                      <InputField
                        label="Taubin Mu"
                        value={parameters.taubinMu}
                        onChange={(value) => updateParameter('taubinMu', value)}
                        min={-0.99}
                        max={-0.01}
                        step={0.01}
                        help="Taubin smoothing mu parameter"
                      />
                    </>
                  )}
                  {(parameters.smoothingType === 'feature_preserving' || parameters.preserveFeatures) && (
                    <>
                      <CheckboxField
                        label="Preserve Features"
                        checked={parameters.preserveFeatures}
                        onChange={(value) => updateParameter('preserveFeatures', value)}
                        help="Preserve sharp features during smoothing"
                      />
                      <InputField
                        label="Feature Angle"
                        value={parameters.featureAngle}
                        onChange={(value) => updateParameter('featureAngle', value)}
                        min={1}
                        max={179}
                        help="Feature edge angle threshold in degrees"
                      />
                    </>
                  )}
                </div>
                <CheckboxField
                  label="Show Mesh Quality Metrics"
                  checked={parameters.meshQuality}
                  onChange={(value) => updateParameter('meshQuality', value)}
                  help="Display detailed mesh quality information"
                />
              </div>
            )}

            <div className="border-t pt-4 space-y-4">
              <h4 className="font-medium text-gray-900">Background Options</h4>
              <CheckboxField
                label="Add Background"
                checked={parameters.background}
                onChange={(value) => updateParameter('background', value)}
                help="Add a solid rectangular background behind the simulation"
              />
              {parameters.background && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <InputField
                    label="Background Depth"
                    value={parameters.backgroundDepth}
                    onChange={(value) => updateParameter('backgroundDepth', value)}
                    min={0.1}
                    step={0.1}
                    help="Depth/thickness of the background layer"
                  />
                  <InputField
                    label="Background Margin"
                    value={parameters.backgroundMargin}
                    onChange={(value) => updateParameter('backgroundMargin', value)}
                    min={0}
                    max={1}
                    step={0.01}
                    help="Background margin as fraction of simulation bounds"
                  />
                  <CheckboxField
                    label="Add Border"
                    checked={parameters.backgroundBorder}
                    onChange={(value) => updateParameter('backgroundBorder', value)}
                    help="Add a raised border around the background edges"
                  />
                  {parameters.backgroundBorder && (
                    <>
                      <InputField
                        label="Border Height"
                        value={parameters.borderHeight}
                        onChange={(value) => updateParameter('borderHeight', value)}
                        min={0.1}
                        step={0.1}
                        help="Height of the border walls above the background"
                      />
                      <InputField
                        label="Border Thickness"
                        value={parameters.borderThickness}
                        onChange={(value) => updateParameter('borderThickness', value)}
                        min={0.1}
                        step={0.1}
                        help="Thickness of the border walls"
                      />
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </SectionHeader>

        {/* Output Parameters */}
        <SectionHeader title="Output Parameters" section="output">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InputField
              label="Output Filename"
              type="text"
              value={parameters.output}
              onChange={(value) => updateParameter('output', value)}
              help="Output STL filename (must end with .stl)"
              fieldKey="output"
            />
            <div className="space-y-2">
              <CheckboxField
                label="Verbose Output"
                checked={parameters.verbose}
                onChange={(value) => updateParameter('verbose', value)}
                help="Show detailed progress information"
              />
              <CheckboxField
                label="Quiet Mode"
                checked={parameters.quiet}
                onChange={(value) => updateParameter('quiet', value)}
                help="Suppress progress output"
              />
            </div>
          </div>
        </SectionHeader>

        {/* Advanced Parameters */}
        <SectionHeader title="Advanced Parameters" section="advanced">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <InputField
              label="Speed Min"
              value={parameters.speedMin || ''}
              onChange={(value) => updateParameter('speedMin', value || undefined)}
              min={0}
              step={0.1}
              help="Minimum speed for initial actors"
            />
            <InputField
              label="Speed Max"
              value={parameters.speedMax || ''}
              onChange={(value) => updateParameter('speedMax', value || undefined)}
              min={0}
              step={0.1}
              help="Maximum speed for initial actors"
            />
            <InputField
              label="Spawn Speed Randomization"
              value={parameters.spawnSpeedRandomization}
              onChange={(value) => updateParameter('spawnSpeedRandomization', value)}
              min={0}
              max={1}
              step={0.01}
              help="Factor for randomizing spawned actor speeds"
            />
            <InputField
              label="Initial Diameter"
              value={parameters.initialDiameter}
              onChange={(value) => updateParameter('initialDiameter', value)}
              min={1}
              step={0.1}
              help="Initial circle diameter for actor placement"
            />
            <InputField
              label="Death Probability"
              value={parameters.deathProbability}
              onChange={(value) => updateParameter('deathProbability', value)}
              min={0}
              max={1}
              step={0.001}
              help="Age-based death probability per step"
            />
            <InputField
              label="Spawn Probability"
              value={parameters.spawnProbability}
              onChange={(value) => updateParameter('spawnProbability', value)}
              min={0}
              max={1}
              step={0.001}
              help="Probability of spawning new actors"
            />
            <InputField
              label="Direction Deviation"
              value={parameters.directionDeviation}
              onChange={(value) => updateParameter('directionDeviation', value)}
              min={0}
              max={3.14159}
              step={0.01}
              help="Maximum direction deviation in radians"
            />
          </div>
        </SectionHeader>

        {/* Submit Button */}
        <div className="pt-6 border-t">
          <button
            type="submit"
            disabled={disabled}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {disabled ? 'Generating Model...' : 'Generate 3D Model'}
          </button>
        </div>
      </form>
    </div>
  );
}