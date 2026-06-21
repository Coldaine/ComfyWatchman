// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

// Add constant for localStorage key - used to persist interface state between sessions
export const PARAM_DEBUG_STORAGE_KEY = 'parameter_debug_state';

/**
 * Saves parameter debug state to localStorage
 */
export const saveStateToLocalStorage = (state: any) => {
  try {
    localStorage.setItem(PARAM_DEBUG_STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.error('Error saving parameter debug state:', error);
  }
};

/**
 * Loads parameter debug state from localStorage
 */
export const loadStateFromLocalStorage = () => {
  try {
    const savedState = localStorage.getItem(PARAM_DEBUG_STORAGE_KEY);
    if (savedState) {
      return JSON.parse(savedState);
    }
  } catch (error) {
    console.error('Error loading parameter debug state:', error);
  }
  return null;
};

/**
 * Clears parameter debug state from localStorage
 */
export const clearStateFromLocalStorage = () => {
  try {
    localStorage.removeItem(PARAM_DEBUG_STORAGE_KEY);
  } catch (error) {
    console.error('Error clearing parameter debug state:', error);
  }
}; 