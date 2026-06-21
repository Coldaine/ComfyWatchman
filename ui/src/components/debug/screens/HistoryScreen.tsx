/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-05-15 15:30:33
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-05-15 18:42:45
 * @FilePath: /comfyui_copilot/ui/src/components/debug/screens/HistoryScreen.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';
import { HistoryItem, formatDate, formatNodeNameWithParams } from '../utils/historyUtils';

interface HistoryScreenProps {
  historyItems: HistoryItem[];
  onViewHistoryItem: (historyItem: HistoryItem) => void;
  onClose: () => void;
}

export const HistoryScreen: React.FC<HistoryScreenProps> = ({
  historyItems,
  onViewHistoryItem,
  onClose
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex flex-col h-full">
      <div className="mb-4 border-b pb-2 flex justify-between items-center">
        <div>
          <h3 className="text-base font-medium text-gray-800">Experiments History</h3>
          <p className="text-xs text-gray-500">Last {historyItems.length} experiments</p>
        </div>
        <button 
          className="text-gray-400 hover:text-gray-600"
          onClick={onClose}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      {historyItems.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
          No history items found
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          {historyItems.map((item) => (
            <div 
              key={item.id} 
              className="border border-gray-200 rounded-lg mb-3 overflow-hidden"
            >
              <div className="bg-gray-50 py-2 px-3 flex items-center justify-between border-b">
                <div className="text-[14px] text-gray-600">
                  {formatDate(item.timestamp)}
                </div>
                <button
                  onClick={() => onViewHistoryItem(item)}
                  className="px-3 py-1 text-xs bg-pink-200 text-pink-700 rounded-md hover:bg-pink-300 transition-colors"
                >
                  view
                </button>
              </div>
              <div className="p-3">
                <div className="text-[10px] font-medium text-gray-700">
                  {formatNodeNameWithParams(item.nodeName, item.params)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 