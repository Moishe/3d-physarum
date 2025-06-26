// ABOUTME: Main form component for simulation parameters organized in collapsible sections
// ABOUTME: Handles form validation, presets, and parameter submission to the simulation API

import React, { useState } from 'react';
import type { SimulationParameters, ParameterPreset } from '../types/simulation';
import { DEFAULT_PARAMETERS, PARAMETER_PRESETS } from '../types/simulation';

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

  const [expandedSections, setExpandedSections] = useState({
    simulation: true,
    model3d: false,
    output: false,
    advanced: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(parameters);
  };

  const updateParameter = (key: keyof SimulationParameters, value: any) => {
    setParameters(prev => ({ ...prev, [key]: value }));
  };

  const applyPreset = (preset: ParameterPreset) => {
    setParameters(prev => ({ ...prev, ...preset.parameters }));
  };

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
    help 
  }: {
    label: string;
    type?: string;
    value: any;
    onChange: (value: any) => void;
    min?: number;
    max?: number;
    step?: number;
    help?: string;
  }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
      />
      {help && <p className="text-xs text-gray-500 mt-1">{help}</p>}
    </div>
  );

  const CheckboxField = ({ 
    label, 
    checked, 
    onChange, 
    help 
  }: {
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    help?: string;
  }) => (
    <div>
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
        />
        <span className="ml-2 text-sm font-medium text-gray-700">{label}</span>
      </label>
      {help && <p className="text-xs text-gray-500 mt-1">{help}</p>}
    </div>
  );

  const SelectField = ({ 
    label, 
    value, 
    options, 
    onChange, 
    help 
  }: {
    label: string;
    value: string;
    options: { value: string; label: string }[];
    onChange: (value: string) => void;
    help?: string;
  }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {help && <p className="text-xs text-gray-500 mt-1">{help}</p>}
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Physarum 3D Model Parameters</h2>
        <p className="text-gray-600">Configure simulation parameters to generate your 3D model</p>
      </div>

      {/* Parameter Presets */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Quick Presets</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {PARAMETER_PRESETS.map(preset => (
            <button
              key={preset.name}
              type="button"
              onClick={() => applyPreset(preset)}
              disabled={disabled}
              className="p-3 text-left border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <div className="font-medium text-gray-900">{preset.name}</div>
              <div className="text-sm text-gray-500">{preset.description}</div>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Simulation Parameters */}
        <SectionHeader title="Simulation Parameters" section="simulation">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <InputField
              label="Width"
              value={parameters.width}
              onChange={(value) => updateParameter('width', value)}
              min={10}
              help="Grid width in pixels"
            />
            <InputField
              label="Height"
              value={parameters.height}
              onChange={(value) => updateParameter('height', value)}
              min={10}
              help="Grid height in pixels"
            />
            <InputField
              label="Actors"
              value={parameters.actors}
              onChange={(value) => updateParameter('actors', value)}
              min={1}
              help="Number of Physarum actors"
            />
            <InputField
              label="Steps"
              value={parameters.steps}
              onChange={(value) => updateParameter('steps', value)}
              min={1}
              help="Number of simulation steps"
            />
            <InputField
              label="Decay Rate"
              value={parameters.decay}
              onChange={(value) => updateParameter('decay', value)}
              min={0}
              max={1}
              step={0.001}
              help="Trail decay rate (0.0-1.0)"
            />
            <InputField
              label="View Radius"
              value={parameters.viewRadius}
              onChange={(value) => updateParameter('viewRadius', value)}
              min={0}
              help="Actor sensing radius"
            />
            <InputField
              label="View Distance"
              value={parameters.viewDistance}
              onChange={(value) => updateParameter('viewDistance', value)}
              min={0}
              help="Actor sensing distance"
            />
            <InputField
              label="Speed"
              value={parameters.speed}
              onChange={(value) => updateParameter('speed', value)}
              min={0}
              step={0.1}
              help="Actor movement speed"
            />
            <InputField
              label="Diffusion Rate"
              value={parameters.diffusionRate}
              onChange={(value) => updateParameter('diffusionRate', value)}
              min={0}
              max={1}
              step={0.01}
              help="Pheromone diffusion rate"
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
            />
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <InputField
                label="Layer Height"
                value={parameters.layerHeight}
                onChange={(value) => updateParameter('layerHeight', value)}
                min={0.1}
                step={0.1}
                help="Height of each layer in 3D model"
              />
              <InputField
                label="Threshold"
                value={parameters.threshold}
                onChange={(value) => updateParameter('threshold', value)}
                min={0}
                max={1}
                step={0.01}
                help="Minimum trail strength for 3D inclusion"
              />
              <InputField
                label="Layer Frequency"
                value={parameters.layerFrequency}
                onChange={(value) => updateParameter('layerFrequency', value)}
                min={1}
                help="Capture layer every N steps"
              />
            </div>

            {parameters.smooth && (
              <div className="border-t pt-4 space-y-4">
                <h4 className="font-medium text-gray-900">Smoothing Options</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
                    onChange={(value) => updateParameter('smoothingType', value as any)}
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InputField
              label="Output Filename"
              type="text"
              value={parameters.output}
              onChange={(value) => updateParameter('output', value)}
              help="Output STL filename (must end with .stl)"
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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