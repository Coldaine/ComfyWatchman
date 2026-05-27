// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

export function generateUUID(): string {
    // 检查是否支持 crypto.randomUUID()
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    
    // 降级方案：手动实现 UUID v4
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
} 