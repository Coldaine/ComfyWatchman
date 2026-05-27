// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { generateUUID } from '../../../utils/uuid';
import { clearStateFromLocalStorage } from './localStorageUtils';
import { WorkflowChatAPI } from '../../../apis/workflowChatApi';
import { applyNodeParameters } from '../../../utils/graphUtils';

/**
 * 重置所有状态变量
 */
export const resetAllStates = (
  setCurrentScreen: React.Dispatch<React.SetStateAction<number>>,
  setSelectedParams: React.Dispatch<React.SetStateAction<{[key: string]: boolean}>>,
  setTask_id: React.Dispatch<React.SetStateAction<string>>,
  cleanupPolling: () => void,
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>,
  setIsCompleted: React.Dispatch<React.SetStateAction<boolean>>,
  setCompletedCount: React.Dispatch<React.SetStateAction<number>>,
  setTotalCount: React.Dispatch<React.SetStateAction<number>>,
  setSelectedImageIndex: React.Dispatch<React.SetStateAction<number | null>>,
  setGeneratedImages: React.Dispatch<React.SetStateAction<any[]>>,
  setParamTestValues: React.Dispatch<React.SetStateAction<{[nodeId: string]: {[paramName: string]: any[]}}>>,
  setOpenDropdowns: React.Dispatch<React.SetStateAction<{[key: string]: boolean | {isOpen: boolean, x: number, y: number}}>>,
  setSearchTerms: React.Dispatch<React.SetStateAction<{[key: string]: string}>>,
  setInputValues: React.Dispatch<React.SetStateAction<{[nodeId_paramName: string]: {min?: string, max?: string, step?: string}}>>,
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>,
  setErrorMessage: React.Dispatch<React.SetStateAction<string | null>>,
  setNotificationVisible: React.Dispatch<React.SetStateAction<boolean>>,
  setModalVisible: React.Dispatch<React.SetStateAction<boolean>>,
  setModalImageUrl: React.Dispatch<React.SetStateAction<string>>,
  setModalImageParams: React.Dispatch<React.SetStateAction<{ [key: string]: any } | null>>,
  setTextInputs: React.Dispatch<React.SetStateAction<{[nodeId_paramName: string]: string[]}>>,
  setAiWritingModalVisible: React.Dispatch<React.SetStateAction<boolean>>,
  setAiWritingModalText: React.Dispatch<React.SetStateAction<string>>,
  setAiGeneratedTexts: React.Dispatch<React.SetStateAction<string[]>>,
  setAiWritingLoading: React.Dispatch<React.SetStateAction<boolean>>,
  setAiWritingNodeId: React.Dispatch<React.SetStateAction<string>>,
  setAiWritingParamName: React.Dispatch<React.SetStateAction<string>>,
  setAiWritingError: React.Dispatch<React.SetStateAction<string | null>>,
  setAiSelectedTexts: React.Dispatch<React.SetStateAction<{[key: string]: boolean}>>,
  clearStorage: boolean = false
) => {
  setCurrentScreen(0);
  setSelectedParams({
    Steps: true,
    CFG: true,
    sampler_name: true,
    threshold: false,
    prompt: false
  });
  // Reset task_id
  setTask_id(generateUUID());
  cleanupPolling();
  setIsProcessing(false);
  setIsCompleted(false);
  setCompletedCount(0);
  setTotalCount(12);
  setSelectedImageIndex(null);
  setGeneratedImages(Array(12).fill(null).map((_, i) => ({
    url: `https://source.unsplash.com/random/300x300?sig=${Math.random()}`,
    params: {
      step: i % 3 === 0 ? 5 : i % 3 === 1 ? 10 : 15,
      sampler_name: 'euler',
      cfg: 1
    }
  })));
  setParamTestValues({});
  setOpenDropdowns({});
  setSearchTerms({});
  setInputValues({});
  setCurrentPage(1);
  setErrorMessage(null);
  setNotificationVisible(false);
  setModalVisible(false);
  setModalImageUrl('');
  setModalImageParams(null);
  // Reset text inputs
  setTextInputs({});
  setAiWritingModalVisible(false);
  setAiWritingModalText('');
  setAiGeneratedTexts([]);
  setAiWritingLoading(false);
  setAiWritingNodeId('');
  setAiWritingParamName('');
  setAiWritingError(null);
  setAiSelectedTexts({});
  
  // Clear localStorage if requested (only when explicitly closing the interface)
  if (clearStorage) {
    clearStateFromLocalStorage();
  }
};

/**
 * 处理选择图像
 */
export const handleSelectImage = (
  index: number,
  setSelectedImageIndex: React.Dispatch<React.SetStateAction<number | null>>,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  setSelectedImageIndex(index);
};

/**
 * 处理应用选中的图像配置
 */
export const handleApplySelected = async (
  selectedImageIndex: number | null,
  generatedImages: any[],
  app: any,
  task_id: string,
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}},
  setNotificationVisible: React.Dispatch<React.SetStateAction<boolean>>,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  if (selectedImageIndex !== null) {
    console.log(`Applied image ${selectedImageIndex + 1} with parameters:`, generatedImages[selectedImageIndex].params);

    // Send tracking event
    let count_temp = 1;
    // Calculate total parameter combinations
    if (paramTestValues) {
      for (const nodeId in paramTestValues) {
        if (paramTestValues[nodeId]) {
          for (const paramName in paramTestValues[nodeId]) {
            const paramOptions = paramTestValues[nodeId][paramName];
            if (paramOptions) {
              let optionsCount = 1;
              if (Array.isArray(paramOptions)) {
                optionsCount = paramOptions.length > 0 ? paramOptions.length : 1;
              } else if (typeof paramOptions === 'object' && paramOptions !== null) {
                // Handle both numeric and string keys in objects
                optionsCount = Object.keys(paramOptions).length > 0 ? Object.keys(paramOptions).length : 1;
              }
              count_temp = count_temp * optionsCount;
            }
          }
        }
      }
    }

    WorkflowChatAPI.trackEvent({
        event_type: 'parameter_debug_apply',
        message_type: 'parameter_debug',
        message_id: task_id,
        data: {
            workflow: (await app.graphToPrompt()).output,
            selected_params: generatedImages[selectedImageIndex].params,
            all_params: paramTestValues,
            count: count_temp
        }
    });

    // Apply selected image parameters to canvas
    const selectedParams = generatedImages[selectedImageIndex].params;
    
    // Use structured parameter format
    if (selectedParams.nodeParams) {
      // 使用通用的节点参数应用函数
      const success = applyNodeParameters(selectedParams.nodeParams);
      
      if (success) {
        console.log('[stateManagementUtils] Successfully applied selected parameters to canvas');
        
        // Show notification message
        setNotificationVisible(true);
        
        // Hide notification after 3 seconds
        setTimeout(() => {
          setNotificationVisible(false);
        }, 3000);
      } else {
        console.warn('[stateManagementUtils] Failed to apply selected parameters to canvas');
      }
    }
  }
};

/**
 * 处理关闭
 */
export const handleClose = (
  currentScreen: number,
  selectedNode: any[],
  nodeIndex: number | undefined,
  dispatch: any,
  onClose: (() => void) | undefined,
  resetAllStates: (clearStorage: boolean) => void,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  
  // Screen 2: Close individual node card
  if (currentScreen === 1 && nodeIndex !== undefined) {
    // Remove the node at specified index
    const newSelectedNodes = [...selectedNode];
    const removedNode = newSelectedNodes[nodeIndex];
    newSelectedNodes.splice(nodeIndex, 1);
    
    // If no nodes left, return to original screen
    if (newSelectedNodes.length === 0) {
      if (onClose) {
        // Clear screen state from context when closing
        dispatch({ type: 'SET_SCREEN_STATE', payload: null });
        // Clear all state variables and localStorage
        resetAllStates(true); // Pass true to clear localStorage
        // Call provided onClose to reset the interface
        onClose();
      }
    } else {
      // Update the context with the new selected nodes
      dispatch({ type: 'SET_SELECTED_NODE', payload: newSelectedNodes });
    }
    return;
  }
  
  // Screen 3, 4, 5 or original: Close the entire interface
  if (onClose) {
    // Clear screen state from context when closing
    dispatch({ type: 'SET_SCREEN_STATE', payload: null });
    // Clear all state variables and localStorage
    resetAllStates(true); // Pass true to clear localStorage
    // Use the provided onClose callback
    onClose();
  }
}; 