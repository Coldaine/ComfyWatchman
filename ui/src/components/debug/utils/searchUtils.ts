// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';
import { StateKey } from '../ParameterDebugInterfaceNew';

/**
 * Process search input
 */
export const handleSearch = (
  nodeId: string, 
  paramName: string, 
  term: string,
  searchTerms: {[key: string]: string},
  updateState: (key: StateKey, value: any) => void
) => {
  const searchKey = `${nodeId}_${paramName}`;
  updateState(StateKey.SearchTerms, {
    ...searchTerms,
    [searchKey]: term
  })
};

/**
 * Handle select all functionality
 */
export const handleSelectAll = (
  nodeId: string, 
  paramName: string, 
  values: any[],
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  updateParamTestValues: (nodeId: string, paramName: string, values: any[]) => void
) => {
  // Ensure nodeID exists
  if (!paramTestValues[nodeId]) {
    updateParamTestValues(nodeId, paramName, values);
    return;
  }
  
  // Get current values
  const currentValues = paramTestValues[nodeId][paramName] || [];
  
  // If all values are selected, cancel selecting all, otherwise select all
  if (values.length === currentValues.length) {
    updateParamTestValues(nodeId, paramName, []);
  } else {
    updateParamTestValues(nodeId, paramName, [...values]);
  }
};

/**
 * Handle parameter selection
 */
export const handleParamSelect = (
  param: string,
  selectedParams: {[key: string]: boolean},
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  updateState: (key: StateKey, value: any) => void,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  const isCurrentlySelected = selectedParams[param];
  
  updateState(StateKey.SelectedParams, {
    ...selectedParams,
    [param]: !isCurrentlySelected
  });
  
  // If we're deselecting a parameter, remove its values from paramTestValues
  if (isCurrentlySelected) {
    // Make a copy of the current paramTestValues
    const updatedParamTestValues = { ...paramTestValues };
    
    // For each node
    Object.keys(updatedParamTestValues).forEach(nodeId => {
      // If this parameter exists in this node, remove it
      if (updatedParamTestValues[nodeId][param]) {
        delete updatedParamTestValues[nodeId][param];
      }
    });
    
    // Update the state with cleaned up values
    updateState(StateKey.ParamTestValues, updatedParamTestValues);
  }
}; 