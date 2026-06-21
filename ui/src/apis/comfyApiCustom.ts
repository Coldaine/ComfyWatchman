/*
 * @Author: ai-business-hql ai.bussiness.hql@gmail.com
 * @Date: 2025-02-17 20:53:45
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-08-06 11:27:06
 * @FilePath: /comfyui_copilot/ui/src/apis/comfyApiCustom.ts
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.
// Copyright (C) 2025 ComfyUI-Copilot Authors
// Licensed under the MIT License.

import { api } from "../utils/comfyapp";
import type { ComfyApi } from "@comfyorg/comfyui-frontend-types";

type ObjectInfo = ReturnType<ComfyApi["getNodeDefs"]>;

export async function getObjectInfo(): Promise<ObjectInfo> {
  try {
    const response = await api.fetchApi("/object_info", { method: "GET" });
    return await response.json();
  } catch (error) {
    console.error("Error fetching object info:", error);
    throw error;
  }
}

export async function getInstalledNodes() {
  const objectInfos = await getObjectInfo();
  return Object.keys(objectInfos);
}

/**
 * Get object info for a specific node class
 * @param nodeClass The class name of the node to get info for
 * @returns Promise with the node definition object
 */
export async function getObjectInfoByClass(nodeClass: string): Promise<any> {
  try {
    const response = await fetch(`/object_info/${nodeClass}`, { method: "GET" });
    return await response.json();
  } catch (error) {
    console.error(`Error fetching object info for ${nodeClass}:`, error);
    throw error;
  }
}

export async function runPrompt(json_data: any): Promise<any> {
  const response = await api.fetchApi("/prompt", {
    method: "POST",
    body: JSON.stringify(json_data),
  });
  return await response.json();
}

/**
 * Clear the prompt queue or delete specific queue items
 * 
 * @param options Configuration options
 * @param options.clear If true, clears the entire queue
 * @param options.delete Array of prompt IDs to delete from the queue
 * @returns Promise with the response
 * 
 * @example
 * // Clear the entire queue
 * await manageQueue({ clear: true });
 * 
 * // Delete specific prompts from the queue
 * await manageQueue({ delete: ["prompt-123", "prompt-456"] });
 * 
 * // Both clear the queue and delete specific prompts
 * await manageQueue({ clear: true, delete: ["prompt-789"] });
 */
export async function manageQueue(options: { 
  clear?: boolean; 
  delete?: string[];
}): Promise<Response> {
  try {
    const response = await api.fetchApi("/queue", {
      method: "POST",
      body: JSON.stringify(options),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to manage queue: ${response.status} ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    console.error("Error managing queue:", error);
    throw error;
  }
}


/**
 * Interrupts the current processing/generation
 * 
 * This function sends a request to the server to stop the current
 * processing operation. It's useful for canceling ongoing image generations.
 * 
 * @returns Promise with the response
 * 
 * @example
 * // Interrupt the current generation process
 * await interruptProcessing();
 */
export async function interruptProcessing(): Promise<Response> {
  try {
    const response = await api.fetchApi("/interrupt", {
      method: "POST",
    });
    
    if (!response.ok) {
      throw new Error(`Failed to interrupt processing: ${response.status} ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    console.error("Error interrupting processing:", error);
    throw error;
  }
}


export async function getHistory(promptId: string): Promise<any> {
  try {
    const response = await api.fetchApi(`/history/${promptId}`, { 
      method: "GET" 
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch history: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Error fetching history:", error);
    throw error;
  }
}

