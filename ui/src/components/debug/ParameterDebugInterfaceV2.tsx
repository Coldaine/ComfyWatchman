// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React, { useState, useEffect } from 'react';
import { ParameterDebugInterface as OriginalParameterDebugInterface } from './ParameterDebugInterfaceNew';
import { ParameterDebugInterfaceProps } from './types/parameterDebugTypes';
import { useChatContext } from '../../context/ChatContext';
import { loadStateFromLocalStorage, clearStateFromLocalStorage } from './utils/localStorageUtils';

/**
 * Enhanced version of ParameterDebugInterface with improved architecture
 * 
 * This component:
 * 1. Handles loading/persisting state to/from localStorage
 * 2. Manages context interactions
 * 3. Delegates rendering to the original component
 */
export const ParameterDebugInterface: React.FC<ParameterDebugInterfaceProps> = (props) => {
  const { dispatch } = useChatContext();
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Handle initialization - load saved state if available
  useEffect(() => {
    if (props.visible && !isInitialized) {
      // Attempt to load saved state
      const savedState = loadStateFromLocalStorage();
      if (savedState) {
        // Update context with screen state if available
        if (savedState.screenState) {
          dispatch({ 
            type: 'SET_SCREEN_STATE', 
            payload: {
              currentScreen: savedState.currentScreen,
              isProcessing: savedState.isProcessing,
              isCompleted: savedState.isCompleted
            }
          });
        }
      }
      setIsInitialized(true);
    }
  }, [props.visible, isInitialized, dispatch]);
  
  // Clean up when component unmounts
  useEffect(() => {
    return () => {
      if (!props.visible) {
        dispatch({ type: 'SET_SCREEN_STATE', payload: null });
      }
    };
  }, [props.visible, dispatch]);

  // The original component handles most of the actual work
  return <OriginalParameterDebugInterface {...props} />;
}; 