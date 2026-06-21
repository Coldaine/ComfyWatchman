// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';
import { StateKey } from '../ParameterDebugInterfaceNew';

/**
 * Toggles dropdown open status
 */
export const toggleDropdown = (
  nodeId: string, 
  paramName: string, 
  event: React.MouseEvent,
  openDropdowns: {[key: string]: boolean | {isOpen: boolean, x: number, y: number}},
  setOpenDropdowns: React.Dispatch<React.SetStateAction<{[key: string]: boolean | {isOpen: boolean, x: number, y: number}}>>
) => {
  event.preventDefault();
  event.stopPropagation();
  
  const dropdownKey = `${nodeId}_${paramName}`;
  
  setOpenDropdowns(prev => {
    const isCurrentlyOpen = prev[dropdownKey] && 
      typeof prev[dropdownKey] === 'object' ? 
      (prev[dropdownKey] as {isOpen: boolean}).isOpen : 
      Boolean(prev[dropdownKey]);
    
    if (isCurrentlyOpen) {
      return {
        ...prev,
        [dropdownKey]: false
      };
    } else {
      // Determine dropdown position
      let x = 0;
      let y = 0;
      
      // Try to get position from event target
      if (event.currentTarget) {
        const rect = event.currentTarget.getBoundingClientRect();
        x = rect.left;
        y = rect.bottom;
      } else {
        // If unable to get element position, use mouse click position
        x = event.clientX;
        y = event.clientY + 20; // Display 20px below mouse position
      }
      
      // Ensure dropdown doesn't go out of window bounds
      const windowWidth = window.innerWidth;
      const dropdownWidth = 250; // Estimated dropdown width
      
      if (x + dropdownWidth > windowWidth) {
        x = windowWidth - dropdownWidth - 10; // Ensure distance from right edge at least 10px
      }
      
      if (x < 0) x = 10; // Ensure distance from left edge at least 10px
      
      return {
        ...prev,
        [dropdownKey]: {
          isOpen: true,
          x: x,
          y: y
        }
      };
    }
  });
};

/**
 * Updates parameter test values
 */
export const updateParamTestValues = (
  nodeId: string, 
  paramName: string, 
  values: any[],
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  updateState: (key: StateKey, value: any) => void,
) => {
  const updatedValues = { ...paramTestValues };
  // Ensure nodeID exists
  if (!updatedValues[nodeId]) {
    updatedValues[nodeId] = {};
  }
  // Update specific node and parameter values
  updatedValues[nodeId][paramName] = values;
  updateState(StateKey.ParamTestValues, updatedValues);
};

/**
 * Handles selecting specific test values
 */
export const handleTestValueSelect = (
  nodeId: string, 
  paramName: string, 
  value: any, 
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  updateState: (key: StateKey, value: any) => void,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  const updatedValues = { ...paramTestValues };
  // Ensure nodeID exists
  if (!updatedValues[nodeId]) {
    updatedValues[nodeId] = {};
  }
  
  // Ensure parameter name exists
  if (!updatedValues[nodeId][paramName]) {
    updatedValues[nodeId][paramName] = [];
  }
  
  const currentValues = updatedValues[nodeId][paramName];
  
  if (currentValues.includes(value)) {
    updatedValues[nodeId][paramName] = currentValues.filter(v => v !== value);
  } else {
    updatedValues[nodeId][paramName] = [...currentValues, value];
  }
  updateState(StateKey.ParamTestValues, updatedValues);
}; 