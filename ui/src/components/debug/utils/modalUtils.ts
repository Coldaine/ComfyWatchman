// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';

/**
 * 打开图像模态框
 */
export const openImageModal = (
  imageUrl: string, 
  params: { [key: string]: any }, 
  selectedNodes: any[],
  setModalImageUrl: React.Dispatch<React.SetStateAction<string>>,
  setModalImageParams: React.Dispatch<React.SetStateAction<{ [key: string]: any } | null>>,
  setModalVisible: React.Dispatch<React.SetStateAction<boolean>>,
  event: React.MouseEvent
) => {
  event.preventDefault();
  event.stopPropagation();
  
  // 添加节点名称信息
  const enhancedParams = { ...params };
  
  // 如果有nodeParams，为每个节点添加节点名称
  if (params.nodeParams) {
    // 创建nodeNames映射
    const nodeNames: {[nodeId: string]: string} = {};
    Object.keys(params.nodeParams).forEach(nodeId => {
      // 尝试从selectedNodes中找到对应节点的名称
      const node = selectedNodes.find(n => n.id.toString() === nodeId);
      nodeNames[nodeId] = node ? (node.title || `Node ${nodeId}`) : `Node ${nodeId}`;
    });
    
    // 添加节点名称信息到参数中
    enhancedParams.nodeNames = nodeNames;
  }
  // 如果没有nodeParams但有其他参数，创建一个简单的nodeParams结构
  else if (Object.keys(params).length > 0) {
    // 创建一个模拟的nodeParams结构
    const simpleNode: {[key: string]: any} = {};
    Object.entries(params).forEach(([key, value]) => {
      // 只处理非对象类型的值
      if (typeof value !== 'object' || value === null) {
        simpleNode[key] = value;
      }
    });
    
    if (Object.keys(simpleNode).length > 0) {
      enhancedParams.nodeParams = { 
        default: simpleNode 
      };
      enhancedParams.nodeNames = { 
        default: params.node_name || params.nodeName || "参数" 
      };
    }
  }
  
  setModalImageUrl(imageUrl);
  setModalImageParams(enhancedParams);
  setModalVisible(true);
};

/**
 * 关闭图像模态框
 */
export const closeImageModal = (
  setModalVisible: React.Dispatch<React.SetStateAction<boolean>>,
  event?: React.MouseEvent
) => {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  setModalVisible(false);
}; 