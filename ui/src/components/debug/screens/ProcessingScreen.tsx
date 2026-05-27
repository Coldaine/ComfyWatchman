// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';
import { manageQueue, interruptProcessing } from '../../../apis/comfyApiCustom';
import { StateKey } from '../ParameterDebugInterfaceNew';

interface ProcessingScreenProps {
  selectedNodes: any[];
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}};
  selectedParams: {[key: string]: boolean};
  totalCount: number;
  completedCount: number;
  errorMessage: string | null;
  handleClose: (event?: React.MouseEvent) => void;
  updateState: (key: StateKey, value: any) => void;
  cleanupPolling?: () => void;
}

export const ProcessingScreen: React.FC<ProcessingScreenProps> = ({
  selectedNodes,
  paramTestValues,
  selectedParams,
  totalCount,
  completedCount,
  errorMessage,
  handleClose,
  updateState,
  cleanupPolling
}) => {
  // 处理取消生成
  const handleCancel = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    manageQueue({clear: true});
    interruptProcessing();
    if (cleanupPolling) {
      cleanupPolling();
    }
    updateState(StateKey.IsProcessing, false);
    updateState(StateKey.CurrentScreen, 2);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 relative">
      {/* Semi-transparent overlay */}
      <div className="absolute inset-0 bg-gray-500 bg-opacity-30 flex flex-col items-center justify-center z-10">
        <div className="text-center text-gray-800 bg-white p-4 rounded-lg shadow-lg">
          <div className="mb-2 text-sm font-medium">Processing...</div>
          <div className="text-xs mb-3">Completed {completedCount} of {totalCount} runs</div>
          <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-pink-500 transition-all duration-200"
              style={{ width: `${(completedCount / totalCount) * 100}%` }}
            ></div>
          </div>
          <div className="mt-2 text-xs text-gray-600">
            Already generated {completedCount} images
          </div>
          <button
            onClick={handleCancel}
            className="mt-4 px-3 py-1.5 text-xs bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>

      {/* Background content (same as confirm configuration content) */}
      <div className="mb-4 border-b pb-2 flex justify-between items-center">
        <div>
          <h3 className="text-base font-medium text-gray-800">Confirm Test Configuration</h3>
          <p className="text-xs text-gray-500">
            In the selected parameter combinations, there are {totalCount} total runs. Each run will generate a separate image.
          </p>
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
      
      {/* Display error message */}
      {errorMessage && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-600 text-xs">
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-2">{errorMessage}</div>
          </div>
        </div>
      )}
      
      {selectedNodes.length > 0 ? (
        selectedNodes.map((node, nodeIndex) => {
          const nodeType = node.type || "Unknown Node";
          const widgets = node.widgets || [];
          const nodeId = node.id;
          
          return (
            <div key={nodeIndex} className="border rounded-md mb-4 overflow-hidden">
              <div className="bg-gray-50 px-3 py-2 text-xs font-medium text-gray-700 border-b">
                {nodeType} (ID: {nodeId})
              </div>
              <div className="p-4 space-y-3">
                {widgets.map((widget: any, widgetIndex: number) => {
                  const paramName = widget.name;
                  
                  if (!selectedParams[paramName]) {
                    return null;
                  }
                  
                  const testValues = paramTestValues[nodeId]?.[paramName] || [];
                  const displayValues = Array.isArray(testValues) 
                    ? `[${testValues.join(', ')}]` 
                    : JSON.stringify(testValues);
                    
                  return (
                    <div key={widgetIndex} className={widgetIndex < widgets.length - 1 ? "flex justify-between items-center border-b pb-2" : "flex justify-between items-center"}>
                      <label className="font-medium text-gray-700">{paramName}</label>
                      <div className="flex space-x-2 items-center">
                        <input 
                          type="text" 
                          className="w-64 h-7 border border-gray-300 rounded text-sm px-2 bg-gray-50 cursor-not-allowed text-gray-500" 
                          readOnly 
                          disabled
                          value={displayValues} 
                          onClick={(e) => e.preventDefault()}
                        />
                      </div>
                    </div>
                  );
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
    </div>
  );
}; 