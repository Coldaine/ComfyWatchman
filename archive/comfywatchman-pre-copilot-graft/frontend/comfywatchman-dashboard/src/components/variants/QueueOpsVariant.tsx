import { useMemo, useState } from 'react';
import type { ActivityLogItem, Model, Workflow } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Download,
  FileJson,
  Gauge,
  ListChecks,
  Pause,
  Play,
  RotateCw,
  Search,
  Settings,
  SlidersHorizontal,
  Sparkles,
  X
} from 'lucide-react';
import { clampPercent } from './utils';

interface VariantProps {
  models?: Model[];
  workflows?: Workflow[];
  activityLog?: ActivityLogItem[];
}

type QueueStatus = 'running' | 'queued' | 'review' | 'blocked' | 'done';
type RunMode = 'auto' | 'assist' | 'dry-run';
type RunCheck = [label: string, value: string, ok: boolean];

interface QueueItem {
  id: string;
  title: string;
  source: string;
  status: QueueStatus;
  done: number;
  total: number;
  detail: string;
}

const fallbackWorkflows: Workflow[] = [
  {
    id: 'wf-upscale-batch',
    name: 'Upscale Batch Repair',
    description: 'Repairs missing upscalers before a paused ComfyUI batch resumes.',
    filename: 'upscale-batch-repair.json',
    createdDate: '2026-05-19',
    lastRun: '2026-05-19',
    status: 'missing-models',
    requiredModels: [
      { modelId: 'model-realesrgan', modelName: 'RealESRGAN x4 Plus', available: false },
      { modelId: 'model-sdxl-base', modelName: 'SDXL Base 1.0', available: true }
    ],
    category: ['download', 'upscale'],
    usageCount: 11
  },
  {
    id: 'wf-controlnet-pack',
    name: 'ControlNet Pack Audit',
    description: 'Confirms each referenced ControlNet path exists under the ComfyUI model tree.',
    filename: 'controlnet-pack-audit.json',
    createdDate: '2026-05-18',
    status: 'ready',
    requiredModels: [
      { modelId: 'model-canny', modelName: 'Canny ControlNet XL', available: true },
      { modelId: 'model-depth', modelName: 'Depth ControlNet XL', available: true }
    ],
    category: ['audit'],
    usageCount: 5
  }
];

const fallbackModels: Model[] = [
  {
    id: 'model-realesrgan',
    name: 'RealESRGAN x4 Plus',
    filename: 'RealESRGAN_x4plus.pth',
    type: 'Upscale',
    size: '64 MB',
    sizeBytes: 67000000,
    dateAdded: '2026-05-19',
    status: 'missing',
    path: 'models/upscale_models/RealESRGAN_x4plus.pth',
    associatedWorkflows: ['wf-upscale-batch'],
    usageCount: 11
  },
  {
    id: 'model-canny',
    name: 'Canny ControlNet XL',
    filename: 'controlnet-canny-sdxl.safetensors',
    type: 'ControlNet',
    size: '2.5 GB',
    sizeBytes: 2680000000,
    dateAdded: '2026-05-18',
    status: 'available',
    path: 'models/controlnet/controlnet-canny-sdxl.safetensors',
    associatedWorkflows: ['wf-controlnet-pack'],
    usageCount: 18
  }
];

const fallbackActivity: ActivityLogItem[] = [
  {
    id: 'act-download-1',
    type: 'download',
    message: 'Download lane reserved for RealESRGAN x4 Plus.',
    timestamp: new Date(Date.now() - 6 * 60000).toISOString()
  },
  {
    id: 'act-import-1',
    type: 'import',
    message: 'Imported controlnet-pack-audit.json and matched 2 model references.',
    timestamp: new Date(Date.now() - 21 * 60000).toISOString()
  }
];

const statusLabel: Record<QueueStatus, string> = {
  running: 'Running',
  queued: 'Queued',
  review: 'Needs review',
  blocked: 'Blocked',
  done: 'Done'
};

const statusTone: Record<QueueStatus, string> = {
  running: 'bg-blue-500',
  queued: 'bg-muted-foreground',
  review: 'bg-amber-500',
  blocked: 'bg-red-500',
  done: 'bg-green-500'
};

function MiniProgress({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div className="h-full rounded-full bg-primary" style={{ width: `${clampPercent(value)}%` }} />
    </div>
  );
}

function deriveQueueItems(models: Model[], workflows: Workflow[], activityLog: ActivityLogItem[]): QueueItem[] {
  const missingModelItems = models
    .filter((model) => model.status === 'missing')
    .slice(0, 4)
    .map((model, index) => ({
      id: `download-${model.id}`,
      title: model.name,
      source: model.type,
      status: index === 0 ? 'running' : 'queued',
      done: index === 0 ? 42 : 0,
      total: 100,
      detail: `Download ${model.filename} into ${model.path}`
    }));

  const workflowItems = workflows.slice(0, 4).map((workflow) => {
    const missing = workflow.requiredModels.filter((model) => !model.available).length;
    const done = workflow.requiredModels.length - missing;
    const status: QueueStatus = missing > 0 ? 'review' : 'done';

    return {
      id: `workflow-${workflow.id}`,
      title: workflow.name,
      source: workflow.filename,
      status,
      done,
      total: Math.max(workflow.requiredModels.length, 1),
      detail:
        missing > 0
          ? `${missing} dependency reference needs resolver confirmation`
          : 'All dependencies are present in the ComfyUI tree'
    };
  });

  const activityItems = activityLog
    .filter((item) => item.type === 'error')
    .slice(0, 2)
    .map((item) => ({
      id: `activity-${item.id}`,
      title: 'Resolver exception',
      source: item.type,
      status: 'blocked',
      done: 0,
      total: 1,
      detail: item.message
    }));

  return [...missingModelItems, ...workflowItems, ...activityItems];
}

export default function QueueOpsVariant({
  models = fallbackModels,
  workflows = fallbackWorkflows,
  activityLog = fallbackActivity
}: VariantProps) {
  const [mode, setMode] = useState<RunMode>('assist');
  const [isRunning, setIsRunning] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const queueItems = useMemo(() => deriveQueueItems(models, workflows, activityLog), [activityLog, models, workflows]);
  const selectedItem = queueItems.find((item) => item.id === selectedId) ?? queueItems[0];

  const totals = useMemo(() => {
    const completedUnits = queueItems.reduce((sum, item) => sum + item.done, 0);
    const totalUnits = queueItems.reduce((sum, item) => sum + item.total, 0);
    const blocked = queueItems.filter((item) => item.status === 'blocked' || item.status === 'review').length;
    const downloads = queueItems.filter((item) => item.id.startsWith('download-')).length;

    return {
      progress: totalUnits === 0 ? 100 : clampPercent((completedUnits / totalUnits) * 100),
      blocked,
      downloads,
      count: queueItems.length
    };
  }, [queueItems]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid min-h-screen lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="border-b border-border bg-card lg:border-b-0 lg:border-r">
          <div className="space-y-5 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="rounded-md bg-primary/10 p-2 text-primary">
                  <SlidersHorizontal className="h-5 w-5" />
                </div>
                <div>
                  <h1 className="text-base font-semibold">Queue Operations</h1>
                  <p className="text-xs text-muted-foreground">ComfyWatchman automation lane</p>
                </div>
              </div>
              <Button size="icon" variant="ghost" aria-label="Queue settings">
                <Settings className="h-4 w-4" />
              </Button>
            </div>

            <Card className="gap-3 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Run mode</span>
                <Badge variant="outline">{mode}</Badge>
              </div>
              <div className="grid grid-cols-3 gap-1">
                {(['auto', 'assist', 'dry-run'] as RunMode[]).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setMode(value)}
                    className={`rounded-md border px-2 py-2 text-xs capitalize transition-colors ${
                      mode === value
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-border bg-background hover:bg-accent'
                    }`}
                  >
                    {value}
                  </button>
                ))}
              </div>
              <Button
                className="w-full"
                variant={isRunning ? 'secondary' : 'default'}
                onClick={() => setIsRunning((value) => !value)}
              >
                {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {isRunning ? 'Pause queue' : 'Start queue'}
              </Button>
            </Card>

            <Card className="gap-3 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Status strip</span>
                <Gauge className="h-4 w-4 text-primary" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Badge variant="secondary" className="justify-center gap-1.5 py-1">
                  <Archive className="h-3 w-3" />
                  {models.length} models
                </Badge>
                <Badge variant="secondary" className="justify-center gap-1.5 py-1">
                  <FileJson className="h-3 w-3" />
                  {workflows.length} graphs
                </Badge>
                <Badge variant={totals.blocked > 0 ? 'destructive' : 'secondary'} className="justify-center gap-1.5 py-1">
                  <AlertTriangle className="h-3 w-3" />
                  {totals.blocked} holds
                </Badge>
                <Badge variant="secondary" className="justify-center gap-1.5 py-1">
                  <Download className="h-3 w-3" />
                  {totals.downloads} pulls
                </Badge>
              </div>
            </Card>
          </div>
        </aside>

        <main className="min-w-0 p-4 md:p-6">
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold">Download and readiness queue</h2>
              <p className="text-sm text-muted-foreground">
                A compact operator view for model downloads, workflow audits, and blocked resolver steps.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline">
                <Search className="h-4 w-4" />
                Search sources
              </Button>
              <Button size="sm" variant="outline">
                <RotateCw className="h-4 w-4" />
                Retry held
              </Button>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
            <section className="space-y-4">
              <Card className="p-4">
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Queue progress</p>
                    <p className="text-xs text-muted-foreground">{totals.count} operation cards</p>
                  </div>
                  <span className="text-2xl font-semibold">{totals.progress}%</span>
                </div>
                <MiniProgress value={totals.progress} />
              </Card>

              <div className="space-y-2">
                {queueItems.map((item) => {
                  const progress = item.total === 0 ? 100 : (item.done / item.total) * 100;
                  const isSelected = selectedItem?.id === item.id;

                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      className={`w-full rounded-md border p-4 text-left transition-colors hover:bg-accent ${
                        isSelected ? 'border-primary bg-accent' : 'border-border bg-card'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${statusTone[item.status]}`} />
                        <div className="min-w-0 flex-1 space-y-2">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium">{item.title}</p>
                              <p className="truncate text-xs text-muted-foreground">{item.source}</p>
                            </div>
                            <Badge variant={item.status === 'blocked' ? 'destructive' : 'outline'}>
                              {statusLabel[item.status]}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{item.detail}</p>
                          <div className="flex items-center gap-3">
                            <MiniProgress value={progress} />
                            <span className="w-16 shrink-0 text-right text-xs text-muted-foreground">
                              {item.done}/{item.total}
                            </span>
                          </div>
                        </div>
                        <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <aside className="space-y-4">
              <Card className="p-5">
                {selectedItem ? (
                  <div className="space-y-5">
                    <div>
                      <div className="mb-2 flex items-center gap-2">
                        <Badge variant={selectedItem.status === 'blocked' ? 'destructive' : 'secondary'}>
                          {statusLabel[selectedItem.status]}
                        </Badge>
                        <Badge variant="outline">{selectedItem.source}</Badge>
                      </div>
                      <h3 className="text-lg font-semibold">{selectedItem.title}</h3>
                      <p className="mt-2 text-sm text-muted-foreground">{selectedItem.detail}</p>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Operation progress</span>
                        <span>{clampPercent((selectedItem.done / selectedItem.total) * 100)}%</span>
                      </div>
                      <MiniProgress value={(selectedItem.done / selectedItem.total) * 100} />
                    </div>

                    <div className="grid gap-2">
                      <Button variant="default">
                        <Sparkles className="h-4 w-4" />
                        Promote next step
                      </Button>
                      <Button variant="outline">
                        <RotateCw className="h-4 w-4" />
                        Re-run resolver
                      </Button>
                      <Button variant="ghost">
                        <X className="h-4 w-4" />
                        Remove from queue
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="py-10 text-center text-sm text-muted-foreground">No queue item selected.</div>
                )}
              </Card>

              <Card className="gap-0 overflow-hidden">
                <div className="border-b border-border p-4">
                  <div className="flex items-center gap-2">
                    <ListChecks className="h-4 w-4" />
                    <h3 className="font-medium">Run checks</h3>
                  </div>
                </div>
                <div className="divide-y divide-border">
                  {([
                    ['Inventory cache', 'Current', true],
                    ['Download paths', 'Writable', true],
                    ['Human review', totals.blocked > 0 ? 'Needed' : 'Clear', totals.blocked === 0],
                    ['Queue heartbeat', isRunning ? 'Active' : 'Paused', isRunning]
                  ] satisfies RunCheck[]).map(([label, value, ok]) => (
                    <div key={label} className="flex items-center justify-between gap-3 p-4">
                      <div className="flex min-w-0 items-center gap-2">
                        {ok ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <Clock3 className="h-4 w-4 text-amber-500" />
                        )}
                        <span className="truncate text-sm">{label}</span>
                      </div>
                      <Badge variant={ok ? 'secondary' : 'destructive'}>{value}</Badge>
                    </div>
                  ))}
                </div>
              </Card>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}
