import { useEffect, useMemo, useState } from 'react';
import { ActivityLogItem, Model, Workflow } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Progress } from '../ui/progress';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  Gauge,
  PackageCheck,
  Play,
  ShieldCheck,
  XCircle
} from 'lucide-react';

interface VariantProps {
  models?: Model[];
  workflows?: Workflow[];
  activityLog?: ActivityLogItem[];
}

type ReviewItem = {
  id: string;
  title: string;
  detail: string;
  status: 'approved' | 'review' | 'blocked';
  priority: 'normal' | 'high' | 'urgent';
};

const fallbackModels: Model[] = [
  {
    id: 'juggernaut-xl',
    name: 'Juggernaut XL',
    filename: 'juggernautXL_v9Rdphoto2Lightning.safetensors',
    type: 'Checkpoint',
    size: '6.6 GB',
    sizeBytes: 7086696038,
    dateAdded: '2026-05-07',
    status: 'available',
    path: 'models/checkpoints/juggernautXL_v9Rdphoto2Lightning.safetensors',
    associatedWorkflows: ['review-pack'],
    usageCount: 28
  },
  {
    id: 'depth-anything',
    name: 'Depth Anything ControlNet',
    filename: 'control_v11f1p_sd15_depth.pth',
    type: 'ControlNet',
    size: '1.4 GB',
    sizeBytes: 1503238553,
    dateAdded: '2026-05-07',
    status: 'missing',
    path: 'models/controlnet/control_v11f1p_sd15_depth.pth',
    associatedWorkflows: ['review-pack'],
    usageCount: 6
  }
];

const fallbackWorkflows: Workflow[] = [
  {
    id: 'review-pack',
    name: 'Client Review Render Pack',
    description: 'Batch render workflow that must clear dependency and path checks.',
    filename: 'client_review_render_pack.json',
    createdDate: '2026-05-14',
    status: 'missing-models',
    requiredModels: [
      { modelId: 'juggernaut-xl', modelName: 'Juggernaut XL', available: true },
      { modelId: 'depth-anything', modelName: 'Depth Anything ControlNet', available: false }
    ],
    category: ['batch', 'review']
  }
];

function buildReviewItems(models: Model[], workflows: Workflow[], activityLog: ActivityLogItem[]): ReviewItem[] {
  const missingModels = models.filter((model) => model.status === 'missing');
  const blockedWorkflows = workflows.filter((workflow) => workflow.status === 'missing-models');
  const errors = activityLog.filter((event) => event.type === 'error');

  return [
    {
      id: 'model-coverage',
      title: 'Model coverage',
      detail: missingModels.length === 0 ? 'All referenced models are indexed locally.' : `${missingModels.length} model reference needs resolution.`,
      status: missingModels.length === 0 ? 'approved' : 'blocked',
      priority: missingModels.length > 1 ? 'urgent' : missingModels.length === 1 ? 'high' : 'normal'
    },
    {
      id: 'workflow-readiness',
      title: 'Workflow readiness',
      detail: blockedWorkflows.length === 0 ? 'Every workflow can be launched.' : `${blockedWorkflows.length} workflow is waiting on dependencies.`,
      status: blockedWorkflows.length === 0 ? 'approved' : 'review',
      priority: blockedWorkflows.length > 0 ? 'high' : 'normal'
    },
    {
      id: 'download-plan',
      title: 'Download plan',
      detail: missingModels.length === 0 ? 'No download actions are required.' : 'Generate queued downloads before running ComfyUI.',
      status: missingModels.length === 0 ? 'approved' : 'review',
      priority: missingModels.length > 0 ? 'high' : 'normal'
    },
    {
      id: 'runtime-errors',
      title: 'Runtime errors',
      detail: errors.length === 0 ? 'No recent blocking errors in the activity log.' : `${errors.length} recent error entry needs review.`,
      status: errors.length === 0 ? 'approved' : 'blocked',
      priority: errors.length > 0 ? 'urgent' : 'normal'
    }
  ];
}

function statusConfig(status: ReviewItem['status']) {
  if (status === 'approved') return { label: 'Approved', icon: CheckCircle2, className: 'text-green-600 dark:text-green-400', badge: 'default' as const };
  if (status === 'blocked') return { label: 'Blocked', icon: XCircle, className: 'text-red-600 dark:text-red-400', badge: 'destructive' as const };
  return { label: 'Review', icon: AlertCircle, className: 'text-amber-600 dark:text-amber-400', badge: 'secondary' as const };
}

export default function ReadinessReviewVariant({
  models = fallbackModels,
  workflows = fallbackWorkflows,
  activityLog = []
}: VariantProps) {
  const reviewItems = useMemo(() => buildReviewItems(models, workflows, activityLog), [models, workflows, activityLog]);
  const [selected, setSelected] = useState<string[]>(reviewItems.filter((item) => item.status !== 'approved').map((item) => item.id));
  const approvedCount = reviewItems.filter((item) => item.status === 'approved').length;
  const readinessScore = Math.round((approvedCount / Math.max(reviewItems.length, 1)) * 100);
  const missingModels = models.filter((model) => model.status === 'missing');

  const toggleSelected = (id: string) => {
    setSelected((current) => current.includes(id) ? current.filter((itemId) => itemId !== id) : [...current, id]);
  };

  useEffect(() => {
    const validIds = new Set(reviewItems.map((item) => item.id));
    setSelected((current) => current.filter((id) => validIds.has(id)));
  }, [reviewItems]);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  Readiness Review
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  Review model coverage, workflow launchability, and download actions before running ComfyUI.
                </p>
              </div>
              <Badge variant={readinessScore === 100 ? 'default' : 'secondary'}>{readinessScore}% clear</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-4">
              {[
                { label: 'Models indexed', value: models.filter((model) => model.status === 'available').length, icon: PackageCheck },
                { label: 'Missing assets', value: missingModels.length, icon: Download },
                { label: 'Ready workflows', value: workflows.filter((workflow) => workflow.status === 'ready').length, icon: Play },
                { label: 'Review items', value: reviewItems.length, icon: FileCheck }
              ].map((stat) => {
                const Icon = stat.icon;
                return (
                  <div key={stat.label} className="rounded-lg border p-3">
                    <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                      <Icon className="h-4 w-4" />
                      <span className="text-xs">{stat.label}</span>
                    </div>
                    <div className="text-2xl">{stat.value}</div>
                  </div>
                );
              })}
            </div>

            <div className="rounded-lg border p-4">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <Gauge className="h-4 w-4" />
                  Launch readiness
                </span>
                <span>{readinessScore}%</span>
              </div>
              <Progress value={readinessScore} />
            </div>

            <div className="space-y-3">
              {reviewItems.map((item) => {
                const config = statusConfig(item.status);
                const Icon = config.icon;
                return (
                  <div key={item.id} className="rounded-lg border bg-background p-4">
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={selected.includes(item.id)}
                        onCheckedChange={() => toggleSelected(item.id)}
                        aria-label={`Select ${item.title}`}
                        disabled={item.status === 'approved'}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Icon className={`h-4 w-4 ${config.className}`} />
                          <span className="font-medium">{item.title}</span>
                          <Badge variant={config.badge}>{config.label}</Badge>
                          <Badge variant="outline">{item.priority}</Badge>
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground">{item.detail}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Action Queue
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="text-2xl">{selected.length}</div>
                <div className="text-sm text-muted-foreground">selected review actions</div>
              </div>
              <Button className="w-full" disabled={selected.length === 0}>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Mark selected reviewed
              </Button>
              <Button className="w-full" variant="outline" disabled={missingModels.length === 0}>
                <Download className="mr-2 h-4 w-4" />
                Generate download plan
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Blocked Models</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(missingModels.length > 0 ? missingModels : models.slice(0, 2)).map((model) => (
                <div key={model.id} className="rounded-md border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium">{model.name}</span>
                    <Badge variant={model.status === 'available' ? 'default' : 'destructive'}>{model.status}</Badge>
                  </div>
                  <div className="mt-1 truncate text-xs text-muted-foreground">{model.path}</div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Evidence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(activityLog.slice(0, 3).length > 0 ? activityLog.slice(0, 3) : [
                { id: 'scan', message: 'Workflow scan completed with dependency findings.', timestamp: 'demo', type: 'execution' as const },
                { id: 'plan', message: 'Download plan is waiting for resolver review.', timestamp: 'demo', type: 'import' as const }
              ]).map((event) => (
                <div key={event.id} className="rounded-md border bg-background p-2 text-xs">
                  <div>{event.message}</div>
                  <div className="mt-1 text-muted-foreground">{event.timestamp}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
