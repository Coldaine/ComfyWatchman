// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React, { useState, useEffect, useRef } from 'react';
import { app } from '../../../utils/comfyapp';
import { useChatContext } from '../../../context/ChatContext';

interface ConfirmConfigurationScreenProps {
  selectedNodes: any[];
  paramTestValues: {[nodeId: string]: {[paramName: string]: any[]}};
  selectedParams: {[key: string]: boolean};
  totalCount: number;
  errorMessage: string | null;
  handlePrevious: (event?: React.MouseEvent) => void;
  handleStartGeneration: (event?: React.MouseEvent, selectedNodeId?: number) => void;
  handleClose: (event?: React.MouseEvent) => void;
}

// Define node interface for type safety
export interface ComfyNode {
  id: number;
  type: string;
  widgets?: any[];
  [key: string]: any;
}

export const ConfirmConfigurationScreen: React.FC<ConfirmConfigurationScreenProps> = ({
  selectedNodes,
  paramTestValues,
  selectedParams,
  totalCount,
  errorMessage,
  handlePrevious,
  handleStartGeneration,
  handleClose
}) => {
  // Add state for tracking image nodes and selected node
  const [imageNodeIds, setImageNodeIds] = useState<number[]>([]);
  const [selectedImageNodeId, setSelectedImageNodeId] = useState<number | null>(null);
  const [showNodeSelectionWarning, setShowNodeSelectionWarning] = useState(false);
  
  // Get dispatch from context to track node selection (only using dispatch)
  const { dispatch } = useChatContext();
  
  // Function to find all SaveImage and PreviewImage nodes
  const findImageNodes = () => {
    const nodes = Object.values(app.graph._nodes_by_id) as ComfyNode[];
    const saveNodeIds: number[] = [];
    const previewNodeIds: number[] = [];
    
    for(const node of nodes) {
      if(node.type === "SaveImage") {
        saveNodeIds.push(node.id);
      } else if(node.type === "PreviewImage") {
        previewNodeIds.push(node.id);
      }
    }
    
    // Combine and set state
    const allImageNodeIds = [...saveNodeIds, ...previewNodeIds];
    setImageNodeIds(allImageNodeIds);
    
    // If there's exactly one node, set it as selected
    if(allImageNodeIds.length === 1) {
      setSelectedImageNodeId(allImageNodeIds[0]);
    } else if(allImageNodeIds.length > 1) {
      // If multiple nodes, enable selection warning
      setShowNodeSelectionWarning(true);
      setSelectedImageNodeId(null);
    }
  };
  
  // Effect to find image nodes when component mounts
  useEffect(() => {
    findImageNodes();
  }, []);
  
  useEffect(() => {
    if (selectedNodes?.length > 0) {
      const node = selectedNodes?.find(node => node.type === "SaveImage" || node.type === "PreviewImage")
      if (!!node) {
        setSelectedImageNodeId(node.id)
      }
    }
  }, [selectedNodes])
  // Effect to detect node selection from canvas - using click listener like in Screen 1
  // useEffect(() => {
  //   // Add a listener for node selection via clicks
  //   const handleNodeSelected = () => {
  //     console.log('handleNodeSelected---->', app.canvas.selected_nodes)
  //     if (!app.canvas.selected_nodes) return;
      
  //     const selectedNodesOnCanvas = Object.values(app.canvas.selected_nodes) as ComfyNode[];
  //     if (selectedNodesOnCanvas.length === 0) return;
  //     console.log('selectedNodesOnCanvas-->', selectedNodesOnCanvas)
  //     // Get the first selected node
  //     const selectedNode = selectedNodesOnCanvas[0];
      
  //     if (!selectedNode) return;
      
  //     // Check if selected node is a SaveImage or PreviewImage node
  //     if (selectedNode.type === "SaveImage" || selectedNode.type === "PreviewImage") {
  //       console.log("Selected image node:", selectedNode.id);
  //       // setSelectedImageNodeId(selectedNode.id);
  //       selectedImageNodeId.current = selectedNode.id
  //     }
  //   };
    
  //   // Listen for click events (same as Screen 1)
  //   document.addEventListener('click', handleNodeSelected);
    
  //   return () => {
  //     document.removeEventListener('click', handleNodeSelected);
  //   };
  // }, []);
  
  // Modified start generation function
  const startGenerationWithSelectedNode = (event?: React.MouseEvent) => {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    // If we need node selection but don't have it yet, show warning
    if (imageNodeIds.length > 1 && !selectedImageNodeId) {
      setShowNodeSelectionWarning(true);
      return;
    }
    console.log('selectedImageNodeId-->', selectedImageNodeId)
    // Otherwise, proceed with selected node ID
    handleStartGeneration(event, selectedImageNodeId || undefined);
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="mb-4 border-b pb-2 flex justify-between items-center">
        <div>
          <h3 className="text-base font-medium text-gray-800">Conform combinations</h3>
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
      
      {/* Display node selection warning */}
      {showNodeSelectionWarning && imageNodeIds.length > 1 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-amber-600 text-xs">
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-2">
              {selectedImageNodeId === null 
                ? `Multiple SaveImage and PreviewImage nodes detected with IDs ${imageNodeIds.join(",")}. Please click the node on canvas.`
                : `Current node ID is ${selectedImageNodeId}, please click Start Generation again`}
            </div>
          </div>
        </div>
      )}
      
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
                      <label className="font-medium text-gray-700 text-xs">{paramName}</label>
                      <div className="flex space-x-2 items-center">
                        <input 
                          type="text" 
                          className="w-64 h-7 border border-gray-300 rounded text-xs px-2 bg-gray-50 cursor-not-allowed text-gray-500" 
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
        <div className="border rounded-md mb-4 p-4 text-center text-gray-500 text-xs">
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
          onClick={(e) => startGenerationWithSelectedNode(e)}
          className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
            (imageNodeIds.length > 1 && !selectedImageNodeId) 
              ? "bg-gray-200 text-gray-500 cursor-not-allowed" 
              : "bg-pink-200 text-pink-700 hover:bg-pink-300"
          }`}
          disabled={imageNodeIds.length > 1 && !selectedImageNodeId}
        >
          Generate & Compare
        </button>
      </div>
    </div>
  );
}; 