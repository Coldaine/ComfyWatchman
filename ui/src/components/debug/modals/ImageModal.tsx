// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';

interface ImageModalProps {
  visible: boolean;
  imageUrl: string;
  params?: { [key: string]: any };
  onClose: (event?: React.MouseEvent) => void;
}

export const ImageModal: React.FC<ImageModalProps> = ({
  visible,
  imageUrl,
  params,
  onClose
}) => {
  if (!visible) return null;
  
  // 处理参数信息格式化显示
  const formatParams = () => {
    if (!params || !params.nodeParams) return null;
    
    const nodeElements = Object.entries(params.nodeParams).map(([nodeId, nodeParams]) => {
      // 获取节点名称 (如果存在)
      const nodeName = params.nodeNames?.[nodeId] || // 首先尝试从 nodeNames 中获取
                     (params.selectedNodeInfoMap && params.selectedNodeInfoMap[nodeId]) || // 然后尝试从 selectedNodeInfoMap 获取
                     (nodeId.includes('text') ? 'Text Node' : // 针对特殊节点类型提供更友好名称
                     `Node ${nodeId}`); // 最后使用默认名称
      
      // 渲染每个参数
      const paramElements = Object.entries(nodeParams as Record<string, any>)
        .filter(([_, value]) => typeof value !== 'object' || value === null) // 过滤掉复杂对象类型，但允许null
        .map(([paramName, value]) => (
          <div key={paramName} className="pl-4 text-sm py-1 flex">
            <span className="text-gray-600 dark:text-gray-400 mr-2">-</span>
            <span className="font-medium mr-1">{paramName}:</span> 
            <span className="text-gray-700 dark:text-gray-300 break-all">{String(value)}</span>
          </div>
        ));
      
      return (
        <div key={nodeId} className="mb-4">
          <div className="font-semibold text-pink-600 dark:text-pink-400 text-base py-1 border-b border-gray-200 dark:border-gray-700 mb-2">
            {nodeName}
          </div>
          {paramElements.length > 0 ? (
            paramElements
          ) : (
            <div className="pl-4 text-sm text-gray-500 italic">nodeParams is null</div>
          )}
        </div>
      );
    });
    
    return (
      <div className="overflow-y-auto max-h-full">
        {nodeElements.length > 0 ? nodeElements : (
          <div className="text-sm text-gray-500 italic">nodeParams is null</div>
        )}
      </div>
    );
  };
  
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl flex flex-row w-[90%] max-w-6xl max-h-[90vh] relative m-4 overflow-hidden" 
        onClick={(e) => e.stopPropagation()}
        style={{ display: 'flex', flexDirection: 'row' }} // 强制使用横向flex布局
      >
        <button 
          className="absolute top-2 right-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 p-1 z-10"
          onClick={onClose}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        {/* 左侧图片 */}
        <div className="w-[65%] border-r border-gray-200 dark:border-gray-700">
          <div className="p-4 h-full flex items-center justify-center">
            <img 
              src={imageUrl} 
              alt="Enlarged image" 
              className="max-w-full max-h-[calc(90vh-2rem)] object-contain"
            />
          </div>
        </div>
        
        {/* 右侧参数信息 */}
        <div className="w-[35%] h-full overflow-hidden flex flex-col">
          <div className="p-4 flex-1 overflow-y-auto">
            <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">Parameters</h3>
            
            {/* 显示常规参数 */}
            {params && !params.nodeParams && Object.entries(params)
              .filter(([paramName, value]) => 
                paramName !== 'nodeParams' && 
                typeof value !== 'object'
              )
              .map(([paramName, value]) => (
                <div key={paramName} className="py-1 text-sm text-gray-600 dark:text-gray-300">
                  <span className="font-medium">{paramName}:</span> {String(value)}
                </div>
              ))
            }
            
            {/* 显示节点参数 */}
            <div className="text-sm text-gray-600 dark:text-gray-300">
              {formatParams()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 