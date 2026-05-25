import { useMemo, useState } from 'react';
import { ActivityLogItem, Model, Workflow } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import {
  AlertTriangle,
  Box,
  CheckCircle2,
  GitBranch,
  Layers3,
  Network,
  PanelLeft,
  Route,
  Search,
  Workflow as WorkflowIcon,
  XCircle
} from 'lucide-react';

interface VariantProps {
  models?: Model[];
  workflows?: Workflow[];
  activityLog?: ActivityLogItem[];
}

type StudioNode = {
  id: string;
  label: string;
  detail: string;
  kind: 'workflow' | 'model' | 'resolver';
  status: 'ready' | 'missing' | 'review';
  x: number;
  y: number;
};

const fallbackModels: Model[] = [
  {
    id: 'sdxl-base',
    name: 'SDXL Base 1.0',
    filename: 'sd_xl_base_1.0.safetensors',
    type: 'Checkpoint',
    size: '6.5 GB',
    sizeBytes: 6979321856,
    dateAdded: '2026-05-01',
    status: 'available',
    path: 'models/checkpoints/sd_xl_base_1.0.safetensors',
    associatedWorkflows: ['portrait-pack', 'upscale-pass'],
    usageCount: 42
  },
  {
    id: 'ip-adapter-plus',
    name: 'IP-Adapter Plus',
    filename: 'ip-adapter-plus_sdxl_vit-h.safetensors',
    type: 'Other',
    size: '1.9 GB',
    sizeBytes: 2040109465,
    dateAdded: '2026-05-03',
    status: 'missing',
    path: 'models/ipadapter/ip-adapter-plus_sdxl_vit-h.safetensors',
    associatedWorkflows: ['portrait-pack'],
    usageCount: 9
  },
  {
    id: 'controlnet-depth',
    name: 'ControlNet Depth XL',
    filename: 'diffusers_xl_depth_full.safetensors',
    type: 'ControlNet',
    size: '2.5 GB',
    sizeBytes: 2684354560,
    dateAdded: '2026-05-08',
    status: 'available',
    path: 'models/controlnet/diffusers_xl_depth_full.safetensors',
    associatedWorkflows: ['upscale-pass'],
    usageCount: 17
  }
];

const fallbackWorkflows: Workflow[] = [
  {
    id: 'portrait-pack',
    name: 'Portrait Dependency Pass',
    description: 'Resolve SDXL portrait workflow requirements before launch.',
    filename: 'portrait_dependency_pass.json',
    createdDate: '2026-05-09',
    status: 'missing-models',
    requiredModels: [
      { modelId: 'sdxl-base', modelName: 'SDXL Base 1.0', available: true },
      { modelId: 'ip-adapter-plus', modelName: 'IP-Adapter Plus', available: false }
    ],
    category: ['SDXL', 'portrait']
  },
  {
    id: 'upscale-pass',
    name: 'Upscale Repair Graph',
    description: 'Inspect upscale graph with checkpoint and ControlNet readiness.',
    filename: 'upscale_repair_graph.json',
    createdDate: '2026-05-10',
    status: 'ready',
    requiredModels: [
      { modelId: 'sdxl-base', modelName: 'SDXL Base 1.0', available: true },
      { modelId: 'controlnet-depth', modelName: 'ControlNet Depth XL', available: true }
    ],
    category: ['upscale', 'repair']
  }
];

function buildNodes(models: Model[], workflows: Workflow[]): StudioNode[] {
  const workflowNodes = workflows.slice(0, 3).map((workflow, index) => ({
    id: `workflow-${workflow.id}`,
    label: workflow.name,
    detail: `${workflow.requiredModels.filter((model) => model.available).length}/${workflow.requiredModels.length} models ready`,
    kind: 'workflow' as const,
    status: workflow.status === 'ready' ? 'ready' as const : 'missing' as const,
    x: 8,
    y: 18 + index * 26
  }));

  const modelNodes = models.slice(0, 5).map((model, index) => ({
    id: `model-${model.id}`,
    label: model.name,
    detail: `${model.type} - ${model.size}`,
    kind: 'model' as const,
    status: model.status === 'available' ? 'ready' as const : 'missing' as const,
    x: 54 + (index % 2) * 18,
    y: 12 + index * 16
  }));

  return [
    ...workflowNodes,
    {
      id: 'resolver',
      label: 'ComfyWatchman Resolver',
      detail: 'Search, verify, and queue missing assets',
      kind: 'resolver',
      status: modelNodes.some((node) => node.status === 'missing') ? 'review' : 'ready',
      x: 34,
      y: 42
    },
    ...modelNodes
  ];
}

function statusClasses(status: StudioNode['status']) {
  if (status === 'ready') return 'border-green-500/40 bg-green-500/10 text-green-700 dark:text-green-300';
  if (status === 'missing') return 'border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-300';
  return 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300';
}

export default function GraphStudioVariant({
  models = fallbackModels,
  workflows = fallbackWorkflows,
  activityLog = []
}: VariantProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('resolver');
  const nodes = useMemo(() => buildNodes(models, workflows), [models, workflows]);
  const selectedNode = nodes.find((node) => node.id === selectedNodeId) || nodes[0];
  const readyModels = models.filter((model) => model.status === 'available').length;
  const readyWorkflows = workflows.filter((workflow) => workflow.status === 'ready').length;
  const readinessScore = Math.round(((readyModels + readyWorkflows) / Math.max(models.length + workflows.length, 1)) * 100);
  const recentEvents = activityLog.slice(0, 3);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-primary" />
            <h2 className="text-xl">Graph Studio</h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Explore workflow-to-model dependencies and resolver handoffs before a ComfyUI run.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <PanelLeft className="mr-2 h-4 w-4" />
            Inspector
          </Button>
          <Button size="sm">
            <Search className="mr-2 h-4 w-4" />
            Resolve Missing
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Card className="overflow-hidden">
          <CardHeader className="pb-0">
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                Dependency Map
              </CardTitle>
              <Badge variant="outline">{nodes.length} nodes</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="relative h-[440px] overflow-hidden bg-muted/30">
              <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border))_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border))_1px,transparent_1px)] bg-[size:40px_40px] opacity-40" />
              <svg className="absolute inset-0 h-full w-full" aria-hidden="true">
                {workflows.flatMap((workflow) =>
                  workflow.requiredModels.map((requiredModel, index) => {
                    const source = nodes.find((node) => node.id === `workflow-${workflow.id}`);
                    const target = nodes.find((node) => node.id === `model-${requiredModel.modelId}`);
                    if (!source || !target) return null;
                    return (
                      <line
                        key={`${workflow.id}-${requiredModel.modelId}-${index}`}
                        x1={`${source.x + 10}%`}
                        y1={`${source.y + 5}%`}
                        x2={`${target.x}%`}
                        y2={`${target.y + 5}%`}
                        stroke={requiredModel.available ? 'hsl(var(--primary))' : 'rgb(239 68 68)'}
                        strokeDasharray={requiredModel.available ? '0' : '6 5'}
                        strokeOpacity="0.45"
                        strokeWidth="2"
                      />
                    );
                  })
                )}
              </svg>

              {nodes.map((node) => {
                const Icon = node.kind === 'workflow' ? WorkflowIcon : node.kind === 'model' ? Box : Route;
                const selected = node.id === selectedNodeId;
                return (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => setSelectedNodeId(node.id)}
                    className={`absolute w-48 rounded-lg border p-3 text-left shadow-sm transition hover:shadow-md ${statusClasses(node.status)} ${
                      selected ? 'ring-2 ring-primary' : ''
                    }`}
                    style={{ left: `${node.x}%`, top: `${node.y}%` }}
                  >
                    <div className="flex items-start gap-2">
                      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">{node.label}</div>
                        <div className="mt-1 line-clamp-2 text-xs opacity-80">{node.detail}</div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers3 className="h-4 w-4" />
                Readiness
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Graph launch score</span>
                  <span>{readinessScore}%</span>
                </div>
                <Progress value={readinessScore} />
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg border p-3">
                  <div className="text-2xl">{readyWorkflows}</div>
                  <div className="text-muted-foreground">ready workflows</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-2xl">{models.length - readyModels}</div>
                  <div className="text-muted-foreground">missing models</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Inspector</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className={`rounded-lg border p-3 ${statusClasses(selectedNode.status)}`}>
                <div className="flex items-center gap-2">
                  {selectedNode.status === 'ready' ? <CheckCircle2 className="h-4 w-4" /> : selectedNode.status === 'missing' ? <XCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                  <span className="font-medium">{selectedNode.label}</span>
                </div>
                <p className="mt-2 text-sm opacity-85">{selectedNode.detail}</p>
              </div>
              <div className="space-y-2 text-sm">
                {(recentEvents.length > 0 ? recentEvents : [
                  { id: 'scan', message: 'Workflow scan linked missing model references.', timestamp: 'just now', type: 'import' as const },
                  { id: 'resolve', message: 'Resolver queued Civitai and HuggingFace checks.', timestamp: 'pending', type: 'execution' as const }
                ]).map((event) => (
                  <div key={event.id} className="rounded-md border bg-background p-2">
                    <div>{event.message}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{event.timestamp}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
