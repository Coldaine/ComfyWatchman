// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React, { useEffect } from 'react';
import { StateKey } from '../ParameterDebugInterfaceNew';

interface ConfigureParameterScreenProps {
  selectedNodes: any[];
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}};
  selectedParams: {[key: string]: boolean};
  updateParamTestValues: (nodeId: string, paramName: string, values: any[]) => void;
  toggleDropdown: (nodeId: string, paramName: string, event: React.MouseEvent) => void;
  openDropdowns: {[key: string]: boolean | {isOpen: boolean, x: number, y: number}};
  handleTestValueSelect: (nodeId: string, paramName: string, value: any, event?: React.MouseEvent) => void;
  searchTerms: {[key: string]: string};
  handleSearch: (nodeId: string, paramName: string, term: string) => void;
  handleSelectAll: (nodeId: string, paramName: string, values: any[]) => void;
  handleNext: (event?: React.MouseEvent) => void;
  handlePrevious: (event?: React.MouseEvent) => void;
  handleClose: (event?: React.MouseEvent, nodeIndex?: number) => void;
  inputValues: {[nodeId_paramName: string]: {min?: string, max?: string, step?: string}};
  updateState: (key: StateKey, value: any) => void
  textInputs: {[nodeId_paramName: string]: string[]};
  handleTextInputChange: (nodeId: string, paramName: string, index: number, value: string) => void;
  handleAddTextInput: (nodeId: string, paramName: string) => void;
  handleRemoveTextInput: (nodeId: string, paramName: string, index: number) => void;
  openAiWritingModal: (nodeId: string, paramName: string) => void;
}

export const ConfigureParameterScreen: React.FC<ConfigureParameterScreenProps> = ({
  selectedNodes,
  paramTestValues,
  selectedParams,
  updateParamTestValues,
  toggleDropdown,
  openDropdowns,
  handleTestValueSelect,
  searchTerms,
  handleSearch,
  handleSelectAll,
  handleNext,
  handlePrevious,
  handleClose,
  inputValues,
  updateState,
  textInputs,
  handleTextInputChange,
  handleAddTextInput,
  handleRemoveTextInput,
  openAiWritingModal
}) => {
  // Function to generate numeric test values
  const generateNumericTestValues = (min: number, max: number, step: number, precision: number = 0) => {
    // Ensure all parameters have valid values
    min = isNaN(min) ? 0 : min;
    max = isNaN(max) ? 100 : max;
    step = isNaN(step) || step <= 0 ? 1 : step;
    
    // Ensure max >= min
    if (max < min) {
      max = min;
    }
    
    // Calculate count based on the actual step
    const count = Math.floor((max - min) / step) + 1;
    if (count <= 1) return [min];
    
    // Generate values based on the actual step
    const values = [];
    let current = min;
    
    // Generate all values between min and max using step
    while (current <= max) {
      // Apply precision based on the parameter
      const factor = Math.pow(10, precision);
      const roundedValue = Math.round(current * factor) / factor;
      
      values.push(roundedValue);
      current += step;
    }
    
    return values;
  };
  
  // Initialize default values for numeric parameters when component mounts
  useEffect(() => {
    if (!selectedNodes || selectedNodes.length === 0) return;
    
    // For each selected node
    selectedNodes.forEach(node => {
      const nodeId = node.id.toString();
      const widgets = node.widgets || {};
      const nodeWidgets = Object.values(widgets);
      
      // For each widget in the node
      nodeWidgets.forEach((widget: any) => {
        const paramName = widget.name;
        
        // Only process selected parameters
        if (!selectedParams[paramName]) return;
        
        // Check if we already have values for this parameter
        const hasValues = paramTestValues[nodeId]?.[paramName]?.length > 0;
        
        // If no values exist yet and it's a numeric parameter
        if (!hasValues && widget.type === "number") {
          const min = widget.options?.min || 0;
          const max = widget.options?.max || 100;
          let step = (widget.options?.step || 10) / 10;
          // 添加最小step值检查
          if (step < 0.1) {
            step = 0.1;
          }
          const precision = widget.options?.precision || 0;
          
          // Generate default values
          const defaultValues = generateNumericTestValues(min, max, step, precision);
          
          // Store these values in the state
          if (defaultValues.length > 0) {
            updateParamTestValues(nodeId, paramName, defaultValues);
            
            // Also update the input values state
            const inputKey = `${nodeId}_${paramName}`;
            updateState(StateKey.InputValues, {
              ...inputValues,
              [inputKey]: {
                min: min.toString(),
                max: max.toString(),
                step: step.toString()
              }
            })
          }
        }
        
        // Handle text inputs - Always ensure paramTestValues are in sync with textInputs
        if ((widget.type === "customtext" || widget.type.toLowerCase().includes("text"))) {
          const inputKey = `${nodeId}_${paramName}`;
          const currentTexts = textInputs[inputKey] || [''];
          
          // Always update paramTestValues with current textInputs to ensure they're in sync
          // This ensures text values are maintained throughout the workflow
          if (JSON.stringify(currentTexts) !== JSON.stringify(paramTestValues[nodeId]?.[paramName] || [''])) {
            updateParamTestValues(nodeId, paramName, currentTexts);
          }
        }
      });
    });
  }, [selectedNodes, selectedParams, paramTestValues, textInputs, updateParamTestValues, generateNumericTestValues]);
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="mb-4 border-b pb-2 flex justify-between items-center">
        <div>
          <h3 className="text-base font-medium text-gray-800">Set test values</h3>
          <p className="text-xs text-gray-500">Configure the test values for each parameter</p>
        </div>
        <button 
          className="text-gray-400 hover:text-gray-600"
          onClick={handleClose}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      {selectedNodes.length > 0 ? (
        selectedNodes.map((node, nodeIndex) => {
          const widgets = node.widgets || {};
          const nodeWidgets = Object.values(widgets);
          const nodeId = node.id; // 获取节点ID
          
          return (
            <div key={nodeIndex} className="border rounded-md mb-4 overflow-hidden">
              <div className="bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 border-b flex justify-between items-center">
                <span>{node.type} (ID: {nodeId})</span>
                {/* Add close button for individual node card */}
                <button 
                  className="text-gray-400 hover:text-gray-600"
                  onClick={(e) => handleClose(e, nodeIndex)}
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-4 space-y-4">
                {nodeWidgets.map((widget: any, widgetIndex: number) => {
                  const paramName = widget.name;
                  
                  // Only show selected parameters
                  if (!selectedParams[paramName]) {
                    return null;
                  }

                  // 为每个输入字段创建唯一的键值
                  const inputKey = `${nodeId}_${paramName}`;
                  
                  // Handle text parameter type
                  if (widget.type === "customtext" || widget.type.toLowerCase().includes("text")) {
                    const currentTexts = textInputs[inputKey] || [''];
                    
                    return (
                      <div key={widgetIndex} className="border-b pb-3">
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-xs font-medium text-gray-700">{paramName}:</label>
                          <button
                            className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center hover:bg-blue-200 transition-colors"
                            onClick={() => openAiWritingModal(nodeId, paramName)}
                          >
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                            AI Writing
                          </button>
                        </div>
                        
                        <div className="space-y-2">
                          {currentTexts.map((text, textIndex) => (
                            <div key={textIndex} className="flex items-start">
                              <textarea
                                className={`flex-1 border ${!text ? 'border-red-500' : 'border-gray-300'} rounded p-2 text-xs resize-y`}
                                rows={2}
                                placeholder="Enter text..."
                                value={text}
                                onChange={(e) => handleTextInputChange(nodeId, paramName, textIndex, e.target.value)}
                                required
                              />
                              <button
                                className="ml-2 text-red-500 hover:text-red-700"
                                onClick={() => handleRemoveTextInput(nodeId, paramName, textIndex)}
                                title="Remove"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          ))}
                        </div>
                        
                        <button
                          className="mt-2 px-2 py-1 border border-dashed border-gray-300 rounded text-xs text-gray-600 hover:bg-gray-50 flex items-center"
                          onClick={() => handleAddTextInput(nodeId, paramName)}
                        >
                          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                          Add Text
                        </button>
                      </div>
                    );
                  }
                  
                  if (widget.type === "number") {
                    const min = widget.options?.min || 0;
                    const max = widget.options?.max || 100;
                    const step = (widget.options?.step || 10) / 10;
                    const precision = widget.options?.precision || 0;
                    const defaultValues = generateNumericTestValues(min, max, step, precision);
                    
                    // 获取当前输入状态，如果不存在则初始化
                    const currentInputs = inputValues[inputKey] || {
                      min: min.toString(),
                      max: max.toString(),
                      step: step.toString()
                    };
                    
                    return (
                      <div key={widgetIndex} className="border-b pb-3">
                        <div className="flex justify-between items-center">
                          <label className="text-xs font-medium text-gray-700">{paramName}:</label>
                          <div className="w-4"></div>
                        </div>
                        <div className="flex space-x-2 items-center">
                          <label className="text-xs text-gray-600">Min</label>
                          <input 
                            type="text" 
                            className="w-12 h-6 border border-gray-300 rounded text-xs px-2" 
                            value={currentInputs.min}
                            required
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                            }}
                            onChange={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              const value = e.target.value;
                              
                              // 更新输入状态
                              updateState(StateKey.InputValues, {
                                ...inputValues,
                                [inputKey]: {
                                  ...inputValues[inputKey],
                                  min: value
                                }
                              })
                              
                              // 只有当输入为空或有效时才更新参数值
                              if (value === '' || !isNaN(parseFloat(value))) {
                                const newMin = value === '' ? 0 : parseFloat(value);
                                const newMax = parseFloat(currentInputs.max || max.toString());
                                const newStep = parseFloat(currentInputs.step || step.toString());
                                const newValues = generateNumericTestValues(newMin, newMax, newStep, precision);
                                updateParamTestValues(nodeId, paramName, newValues);
                              }
                            }}
                          />
                          <label className="text-xs text-gray-600">Max</label>
                          <input 
                            type="text" 
                            className="w-12 h-6 border border-gray-300 rounded text-xs px-2" 
                            value={currentInputs.max}
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                            }}
                            required
                            onChange={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              const value = e.target.value;
                              
                              // 更新输入状态
                              updateState(StateKey.InputValues, {
                                ...inputValues,
                                [inputKey]: {
                                  ...inputValues[inputKey],
                                  max: value
                                }
                              })
                              
                              // 只有当输入为空或有效时才更新参数值
                              if (value === '' || !isNaN(parseFloat(value))) {
                                const newMin = parseFloat(currentInputs.min || min.toString());
                                const newMax = value === '' ? newMin : parseFloat(value);
                                const newStep = parseFloat(currentInputs.step || step.toString());
                                const newValues = generateNumericTestValues(newMin, newMax, newStep, precision);
                                updateParamTestValues(nodeId, paramName, newValues);
                              }
                            }}
                          />
                          <label className="text-xs text-gray-600">Step</label>
                          <input 
                            type="text" 
                            className="w-12 h-6 border border-gray-300 rounded text-xs px-2" 
                            value={currentInputs.step}
                            required
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                            }}
                            onChange={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              const value = e.target.value;
                              
                              // 更新输入状态
                              updateState(StateKey.InputValues, {
                                ...inputValues,
                                [inputKey]: {
                                  ...inputValues[inputKey],
                                  step: value
                                }
                              })
                              
                              // 只有当输入为空或有效时才更新参数值
                              if (value === '' || (!isNaN(parseFloat(value)) && parseFloat(value) > 0)) {
                                const newMin = parseFloat(currentInputs.min || min.toString());
                                const newMax = parseFloat(currentInputs.max || max.toString());
                                let newStep = value === '' ? 1 : parseFloat(value);
                                if (newStep < 0.1) {
                                  newStep = 0.1;
                                }
                                const newValues = generateNumericTestValues(newMin, newMax, newStep, precision);
                                updateParamTestValues(nodeId, paramName, newValues);
                              }
                            }}
                          />
                        </div>
                        <div className="mt-1">
                          <label className="text-xs text-gray-600">Test values</label>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {(() => {
                              const values = paramTestValues[nodeId]?.[paramName] || defaultValues;
                              
                              // If 10 values or less, show all of them
                              if (values.length <= 10) {
                                return values.map((value, idx) => (
                                  <div 
                                    key={idx}
                                    className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md flex items-center text-xs cursor-pointer hover:bg-blue-200"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleTestValueSelect(nodeId, paramName, value, e);
                                    }}
                                  >
                                    <span>{value}</span>
                                    <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                  </div>
                                ));
                              } else {
                                // Show first 5, ellipsis, and last 5
                                const firstFive = values.slice(0, 5);
                                const lastFive = values.slice(values.length - 5);
                                
                                return (
                                  <>
                                    {firstFive.map((value, idx) => (
                                      <div 
                                        key={`first-${idx}`}
                                        className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md flex items-center text-xs cursor-pointer hover:bg-blue-200"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleTestValueSelect(nodeId, paramName, value, e);
                                        }}
                                      >
                                        <span>{value}</span>
                                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                      </div>
                                    ))}
                                    
                                    {/* Ellipsis indicator */}
                                    <div className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-md flex items-center text-xs">
                                      ...
                                    </div>
                                    
                                    {lastFive.map((value, idx) => (
                                      <div 
                                        key={`last-${idx}`}
                                        className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md flex items-center text-xs cursor-pointer hover:bg-blue-200"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleTestValueSelect(nodeId, paramName, value, e);
                                        }}
                                      >
                                        <span>{value}</span>
                                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                      </div>
                                    ))}
                                  </>
                                );
                              }
                            })()}
                          </div>
                        </div>
                        <div className="mt-1">
                          <p className="text-xs text-gray-500">Values are distributed evenly between Min and Max</p>
                        </div>
                      </div>
                    );
                  } else if (widget.type === "combo") {
                    const values = widget.options?.values || [];
                    const dropdownKey = `${nodeId}_${paramName}`;
                    
                    // Helper function to get display value, handling both string and object
                    const getDisplayValue = (value: any): string => {
                      if (typeof value === 'string') return value;
                      if (value && typeof value === 'object' && 'name' in value) return value.name;
                      return String(value);
                    };
                    
                    // Helper function to get actual value to store
                    const getValueToStore = (value: any): any => {
                      if (typeof value === 'object' && value !== null && 'name' in value) {
                        return value.name;
                      }
                      return value;
                    };
                    
                    return (
                      <div key={widgetIndex} className="border-b pb-3">
                        <div className="flex justify-between items-center">
                          <label className="text-xs font-medium text-gray-700">{paramName}</label>
                          <div className="relative dropdown-container">
                            <button 
                              className={`appearance-none border ${(paramTestValues[nodeId]?.[paramName] || []).length === 0 ? 'border-red-500' : 'border-gray-300'} rounded px-2 py-0.5 pr-6 text-xs flex items-center bg-white text-gray-700`}
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                toggleDropdown(nodeId, paramName, e);
                              }}
                              data-dropdown={dropdownKey}
                            >
                              <span>
                                {(paramTestValues[nodeId]?.[paramName] || []).length > 0 
                                  ? `${paramName}: ${(paramTestValues[nodeId]?.[paramName] || []).length} selected` 
                                  : `Select ${paramName}`}
                              </span>
                              <div className="ml-2">
                                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                                  <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
                                </svg>
                              </div>
                            </button>
                            
                            {openDropdowns[dropdownKey] && (
                              <div 
                                className="absolute z-[9999] mt-1 w-64 bg-white border border-gray-300 rounded-md shadow-lg dropdown-menu"
                                style={{
                                  position: 'fixed',
                                  top: typeof openDropdowns[dropdownKey] === 'object' ? 
                                    `${(openDropdowns[dropdownKey] as {y: number}).y}px` : '0px',
                                  left: typeof openDropdowns[dropdownKey] === 'object' ? 
                                    `${(openDropdowns[dropdownKey] as {x: number}).x}px` : '0px',
                                  maxHeight: '300px',
                                  overflowY: 'auto',
                                }}
                              >
                                {/* Search box */}
                                <div className="p-2 border-b sticky top-0 bg-white">
                                  <input
                                    type="text"
                                    className="w-full px-2 py-0.5 text-xs border border-gray-300 rounded"
                                    placeholder="Search..."
                                    value={searchTerms[dropdownKey] || ''}
                                    onChange={(e) => {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      handleSearch(nodeId, paramName, e.target.value);
                                    }}
                                    onClick={(e) => {
                                      e.preventDefault();
                                      e.stopPropagation();
                                    }}
                                    autoFocus
                                  />
                                </div>
                                
                                {/* Select all option */}
                                <div 
                                  className="px-3 py-1.5 bg-gray-50 border-b cursor-pointer text-xs flex items-center text-gray-700 hover:bg-gray-100"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    const filteredValues = values.filter((value: any) => 
                                      !searchTerms[dropdownKey] || 
                                      getDisplayValue(value).toLowerCase().includes((searchTerms[dropdownKey] || '').toLowerCase())
                                    );
                                    // Map values to use name property when available
                                    const valuesToStore = filteredValues.map(getValueToStore);
                                    handleSelectAll(nodeId, paramName, valuesToStore);
                                  }}
                                >
                                  <div className={`w-4 h-4 mr-2 border rounded-sm flex items-center justify-center ${
                                    values.length > 0 && 
                                    (paramTestValues[nodeId]?.[paramName] || []).length === values.length 
                                      ? 'bg-blue-500 border-blue-500' 
                                      : (paramTestValues[nodeId]?.[paramName] || []).length > 0 
                                        ? 'bg-blue-500 border-blue-500 opacity-50' 
                                        : 'border-gray-300'
                                  }`}>
                                    {(paramTestValues[nodeId]?.[paramName] || []).length > 0 && (
                                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                      </svg>
                                    )}
                                  </div>
                                  <span className="font-medium">
                                    {values.length > 0 && 
                                    (paramTestValues[nodeId]?.[paramName] || []).length === values.length 
                                      ? 'Deselect All' 
                                      : 'Select All'}
                                  </span>
                                </div>
                                
                                {/* Scrollable option list */}
                                <div className="max-h-60 overflow-y-auto">
                                  {values
                                    .filter((value: any) => 
                                      !searchTerms[dropdownKey] || 
                                      getDisplayValue(value).toLowerCase().includes((searchTerms[dropdownKey] || '').toLowerCase())
                                    )
                                    .map((value: any, i: number) => (
                                      <div 
                                        key={i} 
                                        className="px-3 py-1.5 hover:bg-gray-100 cursor-pointer text-xs flex items-center text-gray-700"
                                        onClick={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          handleTestValueSelect(nodeId, paramName, getValueToStore(value), e);
                                        }}
                                      >
                                        <div className={`w-4 h-4 mr-2 border rounded-sm flex items-center justify-center ${(paramTestValues[nodeId]?.[paramName] || []).includes(getValueToStore(value)) ? 'bg-blue-500 border-blue-500' : 'border-gray-300'}`}>
                                          {(paramTestValues[nodeId]?.[paramName] || []).includes(getValueToStore(value)) && (
                                            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                          )}
                                        </div>
                                        <span className="whitespace-normal overflow-hidden text-ellipsis">{getDisplayValue(value)}</span>
                                      </div>
                                    ))}
                                  
                                  {/* No search results message */}
                                  {values.filter((value: any) => 
                                    !searchTerms[dropdownKey] || 
                                    getDisplayValue(value).toLowerCase().includes((searchTerms[dropdownKey] || '').toLowerCase())
                                  ).length === 0 && (
                                    <div className="px-3 py-4 text-sm text-gray-500 text-center">
                                      No matching options
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="mt-2">
                          <label className="text-xs text-gray-600">Test values</label>
                          {(paramTestValues[nodeId]?.[paramName] || []).length === 0 && (
                            <div className="text-xs text-red-500 mt-1">Please select at least one value</div>
                          )}
                          <div className="mt-1 flex flex-wrap gap-1">
                            {(paramTestValues[nodeId]?.[paramName] || []).map((value: any, idx: number) => (
                              <div 
                                key={idx}
                                className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md flex items-center text-xs"
                              >
                                <span>{value}</span>
                                <svg 
                                  className="w-4 h-4 ml-1 cursor-pointer hover:text-blue-600" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleTestValueSelect(nodeId, paramName, value, e);
                                  }}
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </div>
                            ))}

                          </div>
                        </div>
                      </div>
                    );
                  } else {
                    return (
                      <div key={widgetIndex} className="border-b pb-3">
                        <div className="flex justify-between items-center">
                          <label className="text-xs font-medium text-gray-700">{paramName}</label>
                        </div>
                        <div className="mt-2">
                          <label className="text-xs text-gray-600">Test values</label>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {(paramTestValues[nodeId]?.[paramName] || []).map((value: string, idx: number) => (
                              <div 
                                key={idx}
                                className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md flex items-center text-xs"
                              >
                                <span>{value}</span>
                                <svg 
                                  className="w-4 h-4 ml-1 cursor-pointer hover:text-blue-600" 
                                  fill="none" 
                                  stroke="currentColor" 
                                  viewBox="0 0 24 24"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleTestValueSelect(nodeId, paramName, value, e);
                                  }}
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </div>
                            ))}
                            <button 
                              className="px-2 py-0.5 border border-dashed border-blue-300 text-blue-600 rounded-md text-xs flex items-center hover:bg-blue-50"
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                const newValue = `${paramName}${(paramTestValues[nodeId]?.[paramName] || []).length + 1}`;
                                updateParamTestValues(nodeId, paramName, [...(paramTestValues[nodeId]?.[paramName] || []), newValue]);
                              }}
                            >
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                              </svg>
                              <span>Add</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  }
                })}
              </div>
            </div>
          );
        })
      ) : (
        <div className="border rounded-md mb-4 p-4 text-center text-gray-500">
          No nodes selected. Please select a node in the workflow to configure parameters.
        </div>
      )}
      
      <div className="mt-6 flex justify-between">
        <button
          onClick={(e) => handlePrevious(e)}
          className="px-3 py-1.5 text-xs bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200 transition-colors"
        >
          Previous
        </button>
        <button
          onClick={(e) => handleNext(e)}
          className="px-3 py-1.5 text-xs bg-pink-200 text-pink-700 rounded-md hover:bg-pink-300 transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}; 