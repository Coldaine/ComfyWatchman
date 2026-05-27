// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { StateKey } from "../ParameterDebugInterfaceNew";

/**
 * Updates text input values in the state
 */
export const handleTextInputChange = (
  nodeId: string, 
  paramName: string, 
  index: number, 
  value: string,
  textInputs: {[key: string]: string[]},
  updateState: (key: StateKey, value: any) => void,
) => {
  const textKey = `${nodeId}_${paramName}`;
  
  const currentTexts = [...(textInputs[textKey] || [])];
  currentTexts[index] = value;
  updateState(StateKey.TextInputs, {
    ...textInputs,
    [textKey]: currentTexts.map((text, i) => (i === index ? value : text))
  })
  
  // Also return the current texts with the new value directly
  return currentTexts;
};

/**
 * Adds a new text input
 */
export const handleAddTextInput = (
  nodeId: string, 
  paramName: string,
  textInputs: {[key: string]: string[]},
  updateState: (key: StateKey, value: any) => void,
) => {
  const textKey = `${nodeId}_${paramName}`;
  
  const currentTexts = [...(textInputs[textKey] || [])];
  currentTexts.push('');

  updateState(StateKey.TextInputs, {
    ...textInputs,
    [textKey]: currentTexts
  })
  
  // Return the updated texts
  return currentTexts
};

/**
 * Removes a text input
 */
export const handleRemoveTextInput = (
  nodeId: string, 
  paramName: string, 
  index: number,
  textInputs: {[key: string]: string[]},
  updateState: (key: StateKey, value: any) => void,
) => {
  const textKey = `${nodeId}_${paramName}`;
  
  const currentTexts = [...(textInputs[textKey] || [])];
  currentTexts.splice(index, 1);

  updateState(StateKey.TextInputs, {
    ...textInputs,
    [textKey]: currentTexts
  })
  
  // Return the updated texts
  return currentTexts;
}; 