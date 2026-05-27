import { useEffect } from 'react';
import { app } from '../utils/comfyapp';
import { useChatContext } from '../context/ChatContext';

export function useNodeSelection(enabled: boolean = true) {
  const { dispatch } = useChatContext();

  useEffect(() => {
    if (!enabled) return;
    
    const handleNodeSelected = () => {
      if (!app.canvas.selected_nodes || Object.keys(app.canvas.selected_nodes).length === 0) {
        dispatch({ type: 'SET_SELECTED_NODE', payload: null });
        return;
      }

      // Get the first selected node
      // const selectedNodeId = Object.keys(app.canvas.selected_nodes)[0];
      // const selectedNode = app.canvas.selected_nodes[selectedNodeId];
      
      // if (!selectedNode) return;
      
      // Extract node information
      // const nodeInfo = {
      //   id: selectedNodeId,
      //   title: selectedNode.title,
      //   type: selectedNode.type,
      //   comfyClass: selectedNode.comfyClass || selectedNode.type,
      //   widgets: selectedNode.widgets,
      //   properties: selectedNode.properties,
      //   inputs: selectedNode.inputs,
      //   outputs: selectedNode.outputs
      // };
      
      dispatch({ type: 'SET_SELECTED_NODE', payload: Object.values(app.canvas.selected_nodes) });
    };

    // Listen for selection events
    document.addEventListener('comfy:node_selected', handleNodeSelected);
    return () => {
      document.removeEventListener('comfy:node_selected', handleNodeSelected);
    };
  }, [dispatch, enabled]);
} 