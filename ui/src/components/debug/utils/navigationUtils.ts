// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';
import { StateKey } from '../ParameterDebugInterfaceNew';

/**
 * 处理页面跳转到下一步
 */
export const handleNext = (
  currentScreen: number,
  selectedParams: {[key: string]: boolean},
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  textInputs: {[nodeId_paramName: string]: string[]},
  selectedNodes: any[],
  setErrorMessage: React.Dispatch<React.SetStateAction<string | null>>,
  generateParameterCombinations: (paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}}) => any[],
  updateState: (key: StateKey, value: any) => void,
  event?: React.MouseEvent,
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  // When moving from screen 0 to screen 1, clean up paramTestValues for unselected parameters
  if (currentScreen === 0) {
    // Make a copy of the current paramTestValues
    const updatedParamTestValues = { ...paramTestValues };
    
    // For each node
    Object.keys(updatedParamTestValues).forEach(nodeId => {
      const nodeParams = updatedParamTestValues[nodeId];
      
      // For each parameter in this node
      Object.keys(nodeParams).forEach(paramName => {
        // If this parameter is no longer selected, remove it
        if (!selectedParams[paramName]) {
          delete nodeParams[paramName];
        }
      });
    });
    
    // Update the state with cleaned up values
    // setParamTestValues(updatedParamTestValues);
    updateState(StateKey.ParamTestValues, updatedParamTestValues);
  }
  
  // When moving to the confirmation screen, ensure all text values are properly synchronized
  if (currentScreen === 1) {
    // Ensure textInputs are synced to paramTestValues for all selected nodes
    const updatedParamTestValues = { ...paramTestValues };
    selectedNodes.forEach(node => {
      const nodeId = node.id.toString();
      const widgets = node.widgets || {};
      
      Object.values(widgets).forEach((widget: any) => {
        const paramName = widget.name;
        
        // Only process selected text parameters
        if (selectedParams[paramName] && (widget.type === "customtext" || widget.type.toLowerCase().includes("text"))) {
          const inputKey = `${nodeId}_${paramName}`;
          const currentTexts = textInputs[inputKey] || [''];
          
          // Update paramTestValues with the current text values
          updatedParamTestValues[nodeId] = updatedParamTestValues[nodeId] || {};
          updatedParamTestValues[nodeId][paramName] = currentTexts;
        }
      });
    });
    
    // Update the state with synchronized values
    updateState(StateKey.ParamTestValues, updatedParamTestValues);
    
    // Update totalCount with parameter combinations
    const combinations = generateParameterCombinations(updatedParamTestValues);
    updateState(StateKey.TotalCount, combinations.length);
  }
  
  // Clear error message
  setErrorMessage(null);
  updateState(StateKey.CurrentScreen, Math.min(currentScreen + 1, 2))
};

/**
 * 处理页面跳转到上一步
 */
export const handlePrevious = (
  currentScreen: number,
  selectedNodes: any[],
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  textInputs: {[nodeId_paramName: string]: string[]},
  isCompleted: boolean,
  setErrorMessage: React.Dispatch<React.SetStateAction<string | null>>,
  updateState: (key: StateKey, value: any) => void,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  // Clear error message
  setErrorMessage(null);
  // Reset completed state when going back
  if (isCompleted) {
    updateState(StateKey.IsCompleted, false)
  }
  
  // If going back from screen 1 to 0, clean up any paramTestValues for nodes that are no longer selected
  if (currentScreen === 1) {
    const selectedNodeIds = selectedNodes.map(node => node.id.toString());
    const currentNodeIds = Object.keys(paramTestValues);
    
    // Remove test values for any nodes that are no longer selected
    const updatedParamTestValues = { ...paramTestValues };
    currentNodeIds.forEach(nodeId => {
      if (!selectedNodeIds.includes(nodeId)) {
        delete updatedParamTestValues[nodeId];
      }
    });
    
    updateState(StateKey.ParamTestValues, updatedParamTestValues);
  }
  
  // If returning from the result gallery or confirmation screen, ensure text values are maintained
  if (currentScreen === 2 || isCompleted) {
    // Ensure paramTestValues are correctly synchronized with textInputs
    const updatedParamTestValues = { ...paramTestValues };
    
    // For each text input value, ensure it's properly synced to paramTestValues
    Object.entries(textInputs).forEach(([key, texts]) => {
      if (!texts || texts.length === 0) return;
      
      const [nodeId, paramName] = key.split('_');
      
      // Skip if node doesn't exist in selected nodes
      if (!selectedNodes.some(node => node.id.toString() === nodeId)) return;
      
      // Ensure the node and parameter exist in paramTestValues
      updatedParamTestValues[nodeId] = updatedParamTestValues[nodeId] || {};
      
      // Only update if the values are different to avoid unnecessary state updates
      if (JSON.stringify(updatedParamTestValues[nodeId][paramName]) !== JSON.stringify(texts)) {
        updatedParamTestValues[nodeId][paramName] = texts;
      }
    });

    updateState(StateKey.ParamTestValues, updatedParamTestValues);
  }
  
  updateState(StateKey.CurrentScreen, Math.max(currentScreen - 1, 0));
};

/**
 * 处理页码变化
 */
export const handlePageChange = (
  newPage: number,
  imagesPerPage: number,
  generatedImages: any[],
  updateState: (key: StateKey, value: any) => void,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  updateState(StateKey.CurrentPage, Math.max(1, Math.min(newPage, Math.ceil(generatedImages.length / imagesPerPage))));
}; 