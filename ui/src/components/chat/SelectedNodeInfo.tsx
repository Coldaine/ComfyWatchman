/*
 * @Author: 晴知 qingli.hql@alibaba-inc.com
 * @Date: 2025-02-17 20:53:45
 * @LastEditors: ai-business-hql ai.bussiness.hql@gmail.com
 * @LastEditTime: 2025-04-22 16:43:57
 * @FilePath: /comfyui_copilot/ui/src/components/chat/SelectedNodeInfo.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { app } from "../../utils/comfyapp";

interface SelectedNodeInfoProps {
    nodeInfo: any[];
    onSendWithIntent: (intent: string, ext?: any) => void;
    loading: boolean;
    onSendWithContent: (text: string) => void;
}


function getDownstreamSubgraphExt(nodeInfo: any[]) {
    const selectedNode = nodeInfo[0];
    const nodeTypeSet = new Set<string>();
    
    function findUpstreamNodes(node: any, depth: number) {
        if (!node || depth >= 1) return;
        
        if (node.inputs) {
            for (const input of Object.values(node.inputs)) {
                const linkId = (input as any).link;
                if (linkId && app.graph.links[linkId]) {
                    const originId = app.graph.links[linkId].origin_id;
                    const originNode = app.graph._nodes_by_id[originId];
                    if (originNode) {
                        nodeTypeSet.add(originNode.type);
                        findUpstreamNodes(originNode, depth + 1);
                    }
                }
            }
        }
    }

    if (selectedNode) {
        findUpstreamNodes(selectedNode, 0);
        return [{"type": "upstream_node_types", "data": Array.from(nodeTypeSet)}];
    }

    return null;
}

export function SelectedNodeInfo({ nodeInfo, onSendWithIntent, loading, onSendWithContent }: SelectedNodeInfoProps) {
    console.log('SelectedNodeInfo nodeInfo:', nodeInfo[0]);
    return (
        <div className="mb-3 p-3 rounded-md bg-gray-50 border border-gray-200">
            <div className="text-sm text-gray-700">
                <p>Selected node: {nodeInfo[0].type}</p>
                <div className="flex gap-2 mt-2">
                    <button
                        className="px-3 py-1 text-xs rounded-md bg-blue-50 
                                 text-blue-700 hover:bg-blue-100"
                        onClick={() => onSendWithContent(`Reply in ${navigator.language} language: How does the ${nodeInfo[0].type} node work? I need its official usage guide.`)}
                        disabled={loading}>
                        Usage
                    </button>
                    <button
                        className="px-3 py-1 text-xs rounded-md bg-green-100 
                                 text-green-700 hover:bg-green-200"
                        onClick={() => onSendWithContent(`Reply in ${navigator.language} language: Show me the technical specifications for the ${nodeInfo[0].type} node's inputs and outputs.`)}
                        disabled={loading}>
                        Parameters
                    </button>
                    <button
                        className="px-3 py-1 text-xs rounded-md bg-purple-100 
                                 text-purple-700 hover:bg-purple-200"
                        onClick={() => onSendWithIntent('downstream_subgraph_search', getDownstreamSubgraphExt(nodeInfo))}
                        disabled={loading}>
                        Downstream Nodes
                    </button>
                </div>
            </div>
        </div>
    );
} 