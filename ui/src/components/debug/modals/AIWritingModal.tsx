// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React from 'react';

interface AIWritingModalProps {
  visible: boolean;
  aiWritingModalText: string;
  setAiWritingModalText: React.Dispatch<React.SetStateAction<string>>;
  aiGeneratedTexts: string[];
  aiSelectedTexts: {[key: string]: boolean};
  aiWritingLoading: boolean;
  aiWritingError: string | null;
  handleAiWriting: () => void;
  toggleTextSelection: (textKey: string) => void;
  addSelectedTexts: () => void;
  onClose: () => void;
}

export const AIWritingModal: React.FC<AIWritingModalProps> = ({
  visible,
  aiWritingModalText,
  setAiWritingModalText,
  aiGeneratedTexts,
  aiSelectedTexts,
  aiWritingLoading,
  aiWritingError,
  handleAiWriting,
  toggleTextSelection,
  addSelectedTexts,
  onClose
}) => {
  if (!visible) return null;
  
  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI Writing Assistant</h3>
          <button 
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            onClick={onClose}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-4 overflow-y-auto flex-1">
          <div className="mb-4">
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">Enter text and AI will generate variations</p>
            <textarea 
              className="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white
                bg-gray-50 dark:bg-gray-700 
                placeholder-gray-500 dark:placeholder-gray-400
                focus:border-blue-500 dark:focus:border-blue-400 
                focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20
                focus:outline-none"
              rows={3}
              placeholder="Enter some text here..."
              value={aiWritingModalText}
              onChange={(e) => setAiWritingModalText(e.target.value)}
            />
            
            <button 
              className={`mt-2 px-4 py-2 rounded-lg text-sm flex items-center transition-colors ${
                aiWritingLoading 
                  ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white'
              }`}
              onClick={handleAiWriting}
              disabled={aiWritingLoading}
            >
              {aiWritingLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500 dark:text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                <>Generate</>
              )}
            </button>
          </div>
          
          {aiWritingError && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/20 rounded-md text-red-700 dark:text-red-400 text-sm">
              {aiWritingError}
            </div>
          )}
          
          {aiGeneratedTexts.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Generated variations (select items to add):</p>
              <div className="space-y-2 max-h-[40vh] overflow-y-auto p-2">
                {aiGeneratedTexts.map((text, idx) => (
                  <div key={idx} className="flex items-start border border-gray-200 dark:border-gray-600 rounded-md p-2">
                    <div className="mr-2 mt-1">
                      <div className="relative">
                        <input 
                          type="checkbox" 
                          id={`text${idx+1}`}
                          checked={!!aiSelectedTexts[`text${idx+1}`]}
                          onChange={() => toggleTextSelection(`text${idx+1}`)}
                          className="sr-only" /* Hide the actual checkbox but keep it functional */
                        />
                        <div 
                          className={`h-4 w-4 rounded border ${
                            aiSelectedTexts[`text${idx+1}`] 
                              ? 'bg-blue-600 dark:bg-blue-500 border-blue-600 dark:border-blue-500' 
                              : 'border-gray-300 dark:border-gray-600'
                          } flex items-center justify-center cursor-pointer`}
                          onClick={() => toggleTextSelection(`text${idx+1}`)}
                        >
                          {aiSelectedTexts[`text${idx+1}`] && (
                            <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                    <label htmlFor={`text${idx+1}`} className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer flex-1">
                      {text}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end flex-shrink-0">
          <button 
            className="px-5 py-2.5 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 
            rounded-lg font-medium transition-colors mr-3"
            onClick={onClose}
          >
            Cancel
          </button>
          <button 
            className={`px-5 py-2.5 rounded-lg font-medium transition-colors ${
              Object.values(aiSelectedTexts).every(v => !v)
                ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white'
            }`}
            onClick={addSelectedTexts}
            disabled={Object.values(aiSelectedTexts).every(v => !v)}
          >
            Add Selected
          </button>
        </div>
      </div>
    </div>
  );
}; 