// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { BaseMessage } from "./BaseMessage";

export function LoadingMessage() {
    return (
        <BaseMessage name="Assistant">
            <div className="flex items-center space-x-2 p-4 bg-gray-50 rounded-lg">
                <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm text-gray-500">AI is thinking...</span>
            </div>
        </BaseMessage>
    );
} 