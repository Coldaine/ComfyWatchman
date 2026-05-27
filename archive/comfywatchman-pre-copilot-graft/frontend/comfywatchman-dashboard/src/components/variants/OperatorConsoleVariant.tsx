import { useMemo, useState } from 'react';
import type { ActivityLogItem, Model, Workflow } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  Download,
  FileSearch,
  Gauge,
  HardDrive,
  Layers,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  TerminalSquare,
  Workflow as WorkflowIcon,
  XCircle
} from 'lucide-react';
import { clampPercent } from './utils';

interface VariantProps {
  models?: Model[];
  workflows?: Workflow[];
  activityLog?: ActivityLogItem[];
}

const fallbackModels: Model[] = [
  {
    id: 'model-sdxl-base',
    name: 'SDXL Base 1.0',
    filename: 'sd_xl_base_1.0.safetensors',
    type: 'Checkpoint',
    size: '6.9 GB',
    sizeBytes: 7400000000,
    dateAdded: '2026-05-18',
    status: 'available',
    path: 'models/checkpoints/sd_xl_base_1.0.safetensors',
    associatedWorkflows: ['wf-product-shot'],
    usageCount: 34
  },
  {
    id: 'model-depth-controlnet',
    name: 'Depth ControlNet XL',
    filename: 'controlnet-depth-sdxl.safetensors',
    type: 'ControlNet',
    size: '2.5 GB',
    sizeBytes: 2680000000,
    dateAdded: '2026-05-19',
    status: 'missing',
    path: 'models/controlnet/controlnet-depth-sdxl.safetensors',
    associatedWorkflows: ['wf-product-shot'],
    usageCount: 8
  },
  {
    id: 'model-refiner',
    name: 'SDXL Refiner',
    filename: 'sd_xl_refiner_1.0.safetensors',
    type: 'Checkpoint',
    size: '6.1 GB',
    sizeBytes: 6550000000,
    dateAdded: '2026-05-17',
    status: 'available',
    path: 'models/checkpoints/sd_xl_refiner_1.0.safetensors',
    associatedWorkflows: ['wf-portrait-pass'],
    usageCount: 19
  }
];

const fallbackWorkflows: Workflow[] = [
  {
    id: 'wf-product-shot',
    name: 'Product Shot Recovery',
    description: 'Checks model readiness before restoring queued product renders.',
    filename: 'product-shot-recovery.json',
    createdDate: '2026-05-19',
    lastRun: '2026-05-19',
    status: 'missing-models',
    requiredModels: [
      { modelId: 'model-sdxl-base', modelName: 'SDXL Base 1.0', available: true },
      { modelId: 'model-depth-controlnet', modelName: 'Depth ControlNet XL', available: false }
    ],
    category: ['ops', 'controlnet'],
    usageCount: 22
  },
  {
    id: 'wf-portrait-pass',
    name: 'Portrait Refinement Pass',
    description: 'Ready workflow for face-safe refinement and final upscale.',
    filename: 'portrait-refinement-pass.json',
    createdDate: '2026-05-18',
    lastRun: '2026-05-19',
    status: 'ready',
    requiredModels: [
      { modelId: 'model-sdxl-base', modelName: 'SDXL Base 1.0', available: true },
      { modelId: 'model-refiner', modelName: 'SDXL Refiner', available: true }
    ],
    category: ['ready', 'refiner'],
    usageCount: 15
  }
];

const fallbackActivity: ActivityLogItem[] = [
  {
    id: 'act-scan',
    type: 'import',
    message: 'Workflow import scanned 2 ComfyUI graphs and resolved 3 model references.',
    timestamp: new Date(Date.now() - 9 * 60000).toISOString()
  },
  {
    id: 'act-download',
    type: 'download',
    message: 'Queued Depth ControlNet XL from HuggingFace fallback search.',
    timestamp: new Date(Date.now() - 17 * 60000).toISOString()
  },
  {
    id: 'act-error',
    type: 'error',
    message: 'Civitai lookup returned low confidence for one checkpoint alias.',
    timestamp: new Date(Date.now() - 43 * 60000).toISOString()
  }
];

function formatRelativeTime(timestamp: string) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return 'unknown';

  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  return `${Math.floor(hours / 24)}d ago`;
}

function ProgressLine({ value, tone = 'primary' }: { value: number; tone?: 'primary' | 'green' | 'amber' }) {
  const colorClass = tone === 'green' ? 'bg-green-500' : tone === 'amber' ? 'bg-amber-500' : 'bg-primary';

  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${clampPercent(value)}%` }} />
    </div>
  );
}

export default function OperatorConsoleVariant({
  models = fallbackModels,
  workflows = fallbackWorkflows,
  activityLog = fallbackActivity
}: VariantProps) {
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(workflows[0]?.id ?? fallbackWorkflows[0].id);

  const stats = useMemo(() => {
    const totalModels = models.length;
    const availableModels = models.filter((model) => model.status === 'available').length;
    const missingModels = totalModels - availableModels;
    const readyWorkflows = workflows.filter((workflow) => workflow.status === 'ready').length;
    const requiredModels = workflows.flatMap((workflow) => workflow.requiredModels);
    const availableRequired = requiredModels.filter((model) => model.available).length;
    const readiness = requiredModels.length === 0 ? 100 : (availableRequired / requiredModels.length) * 100;

    return {
      totalModels,
      availableModels,
      missingModels,
      readyWorkflows,
      readiness: clampPercent(readiness),
      activeDownloads: activityLog.filter((item) => item.type === 'download').length
    };
  }, [activityLog, models, workflows]);

  const selectedWorkflow =
    workflows.find((workflow) => workflow.id === selectedWorkflowId) ?? workflows[0] ?? fallbackWorkflows[0];
  const missingForSelected = selectedWorkflow.requiredModels.filter((model) => !model.available);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card px-4 py-3 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-md bg-primary/10 p-2 text-primary">
              <TerminalSquare className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">ComfyWatchman Operator Console</h1>
              <p className="text-sm text-muted-foreground">
                Workflow readiness, dependency recovery, and download operations
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="gap-1.5">
              <ShieldCheck className="h-3 w-3" />
              Offline inventory ready
            </Badge>
            <Badge variant={stats.missingModels > 0 ? 'destructive' : 'default'} className="gap-1.5">
              {stats.missingModels > 0 ? <AlertCircle className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />}
              {stats.missingModels} missing
            </Badge>
            <Button size="sm" variant="outline">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="grid gap-4 p-4 md:grid-cols-[280px_minmax(0,1fr)] md:p-6 xl:grid-cols-[300px_minmax(0,1fr)_320px]">
        <aside className="space-y-4">
          <Card className="gap-4 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Fleet Readiness</p>
                <p className="text-xs text-muted-foreground">Required model coverage</p>
              </div>
              <Gauge className="h-5 w-5 text-primary" />
            </div>
            <div className="space-y-2">
              <div className="flex items-end justify-between">
                <span className="text-3xl font-semibold">{stats.readiness}%</span>
                <span className="text-xs text-muted-foreground">
                  {stats.availableModels}/{stats.totalModels} local
                </span>
              </div>
              <ProgressLine value={stats.readiness} tone={stats.readiness > 80 ? 'green' : 'amber'} />
            </div>
          </Card>

          <Card className="gap-0 overflow-hidden">
            <div className="border-b border-border p-4">
              <div className="flex items-center gap-2">
                <WorkflowIcon className="h-4 w-4" />
                <h2 className="font-medium">Workflow Queue</h2>
              </div>
            </div>
            <div className="divide-y divide-border">
              {workflows.map((workflow) => {
                const missingCount = workflow.requiredModels.filter((model) => !model.available).length;
                const isSelected = workflow.id === selectedWorkflow.id;

                return (
                  <button
                    key={workflow.id}
                    type="button"
                    onClick={() => setSelectedWorkflowId(workflow.id)}
                    className={`w-full px-4 py-3 text-left transition-colors hover:bg-accent ${
                      isSelected ? 'bg-accent' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {workflow.status === 'ready' ? (
                        <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="mt-0.5 h-4 w-4 text-red-500" />
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{workflow.name}</p>
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{workflow.description}</p>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          <Badge variant={workflow.status === 'ready' ? 'secondary' : 'destructive'}>
                            {workflow.status === 'ready' ? 'Ready' : `${missingCount} missing`}
                          </Badge>
                          <Badge variant="outline">{workflow.requiredModels.length} models</Badge>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </Card>
        </aside>

        <section className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card className="gap-2 p-4">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Ready workflows</span>
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              </div>
              <p className="text-2xl font-semibold">{stats.readyWorkflows}</p>
            </Card>
            <Card className="gap-2 p-4">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Missing models</span>
                <FileSearch className="h-4 w-4 text-amber-500" />
              </div>
              <p className="text-2xl font-semibold">{stats.missingModels}</p>
            </Card>
            <Card className="gap-2 p-4">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Download tasks</span>
                <Download className="h-4 w-4 text-blue-500" />
              </div>
              <p className="text-2xl font-semibold">{stats.activeDownloads}</p>
            </Card>
            <Card className="gap-2 p-4">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Indexed assets</span>
                <Database className="h-4 w-4 text-primary" />
              </div>
              <p className="text-2xl font-semibold">{stats.totalModels}</p>
            </Card>
          </div>

          <Card className="p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge variant={selectedWorkflow.status === 'ready' ? 'default' : 'destructive'}>
                    {selectedWorkflow.status === 'ready' ? 'Ready to run' : 'Recovery needed'}
                  </Badge>
                  <Badge variant="outline">{selectedWorkflow.filename}</Badge>
                </div>
                <h2 className="text-xl font-semibold">{selectedWorkflow.name}</h2>
                <p className="mt-2 max-w-3xl text-sm text-muted-foreground">{selectedWorkflow.description}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="outline">
                  <Search className="h-4 w-4" />
                  Resolve
                </Button>
                <Button size="sm" disabled={selectedWorkflow.status !== 'ready'}>
                  <Play className="h-4 w-4" />
                  Run
                </Button>
              </div>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">Dependency Ledger</h3>
                  <span className="text-xs text-muted-foreground">
                    {selectedWorkflow.requiredModels.length - missingForSelected.length} available
                  </span>
                </div>
                <div className="space-y-2">
                  {selectedWorkflow.requiredModels.map((requiredModel) => (
                    <div
                      key={`${selectedWorkflow.id}-${requiredModel.modelId}`}
                      className="flex items-center justify-between gap-3 rounded-md border border-border bg-background p-3"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        {requiredModel.available ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-amber-500" />
                        )}
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{requiredModel.modelName}</p>
                          <p className="text-xs text-muted-foreground">{requiredModel.modelId}</p>
                        </div>
                      </div>
                      <Badge variant={requiredModel.available ? 'secondary' : 'destructive'}>
                        {requiredModel.available ? 'Available' : 'Missing'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-md border border-border bg-muted/30 p-4">
                <div className="mb-4 flex items-center gap-2">
                  <HardDrive className="h-4 w-4" />
                  <h3 className="text-sm font-medium">Recovery Plan</h3>
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="mb-1 flex justify-between text-xs">
                      <span>Inventory scan</span>
                      <span>100%</span>
                    </div>
                    <ProgressLine value={100} tone="green" />
                  </div>
                  <div>
                    <div className="mb-1 flex justify-between text-xs">
                      <span>Resolver confidence</span>
                      <span>{missingForSelected.length ? '68%' : '94%'}</span>
                    </div>
                    <ProgressLine value={missingForSelected.length ? 68 : 94} tone={missingForSelected.length ? 'amber' : 'green'} />
                  </div>
                  <div className="rounded-md bg-background p-3 text-xs text-muted-foreground">
                    {missingForSelected.length
                      ? `${missingForSelected.length} model download should be reviewed before this graph runs.`
                      : 'All required models are present. This graph can move into the run lane.'}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </section>

        <aside className="space-y-4 md:col-span-2 xl:col-span-1">
          <Card className="gap-0 overflow-hidden">
            <div className="border-b border-border p-4">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                <h2 className="font-medium">Operations Feed</h2>
              </div>
            </div>
            <div className="divide-y divide-border">
              {activityLog.slice(0, 6).map((item) => (
                <div key={item.id} className="flex gap-3 p-4">
                  <div className="mt-0.5 rounded-md bg-muted p-1.5">
                    {item.type === 'download' && <Download className="h-4 w-4 text-blue-500" />}
                    {item.type === 'execution' && <Play className="h-4 w-4 text-green-500" />}
                    {item.type === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
                    {item.type === 'import' && <Layers className="h-4 w-4 text-primary" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <Badge variant="outline">{item.type}</Badge>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        <Clock className="mr-1 inline h-3 w-3" />
                        {formatRelativeTime(item.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{item.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </aside>
      </main>
    </div>
  );
}
