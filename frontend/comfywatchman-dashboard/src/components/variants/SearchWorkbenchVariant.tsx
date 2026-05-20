import { useMemo, useState } from 'react';
import { ActivityLogItem, Model, Workflow } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Bot,
  CheckCircle2,
  Cloud,
  Database,
  FileSearch,
  Filter,
  History,
  Link2,
  Loader2,
  Search,
  Sparkles,
  Upload,
  Wand2
} from 'lucide-react';

interface VariantProps {
  models?: Model[];
  workflows?: Workflow[];
  activityLog?: ActivityLogItem[];
}

type Candidate = {
  id: string;
  name: string;
  source: 'Local' | 'Civitai' | 'HuggingFace';
  confidence: number;
  reason: string;
  tags: string[];
};

const fallbackModels: Model[] = [
  {
    id: 'realvisxl',
    name: 'RealVisXL V5.0',
    filename: 'realvisxlV50_v50Bakedvae.safetensors',
    type: 'Checkpoint',
    size: '6.4 GB',
    sizeBytes: 6871947673,
    dateAdded: '2026-05-11',
    status: 'available',
    path: 'models/checkpoints/realvisxlV50_v50Bakedvae.safetensors',
    associatedWorkflows: ['catalog-scene'],
    usageCount: 31
  },
  {
    id: 'animatediff-motion',
    name: 'AnimateDiff Motion Adapter',
    filename: 'mm_sdxl_v10_beta.ckpt',
    type: 'Other',
    size: '1.7 GB',
    sizeBytes: 1825361100,
    dateAdded: '2026-05-12',
    status: 'missing',
    path: 'models/animatediff/mm_sdxl_v10_beta.ckpt',
    associatedWorkflows: ['motion-test'],
    usageCount: 4
  }
];

const fallbackWorkflows: Workflow[] = [
  {
    id: 'catalog-scene',
    name: 'Catalog Scene Builder',
    description: 'Product image generation workflow that prefers photoreal checkpoints.',
    filename: 'catalog_scene_builder.json',
    createdDate: '2026-05-13',
    status: 'ready',
    requiredModels: [{ modelId: 'realvisxl', modelName: 'RealVisXL V5.0', available: true }],
    category: ['product', 'photoreal']
  },
  {
    id: 'motion-test',
    name: 'Motion Adapter Test',
    description: 'Animation smoke test with missing AnimateDiff adapter.',
    filename: 'motion_adapter_test.json',
    createdDate: '2026-05-13',
    status: 'missing-models',
    requiredModels: [{ modelId: 'animatediff-motion', modelName: 'AnimateDiff Motion Adapter', available: false }],
    category: ['animation']
  }
];

function buildCandidates(models: Model[], workflows: Workflow[], query: string): Candidate[] {
  const missing = models.filter((model) => model.status === 'missing');
  const local = models.filter((model) => model.status === 'available');
  const basis = query.trim() || missing[0]?.name || workflows.find((workflow) => workflow.status === 'missing-models')?.name || 'SDXL model';

  return [
    ...local.slice(0, 2).map((model) => ({
      id: `local-${model.id}`,
      name: model.name,
      source: 'Local' as const,
      confidence: model.associatedWorkflows.length > 0 ? 92 : 78,
      reason: `Already indexed at ${model.path}`,
      tags: [model.type, model.size]
    })),
    ...missing.slice(0, 2).map((model) => ({
      id: `civitai-${model.id}`,
      name: `${model.name} candidate`,
      source: 'Civitai' as const,
      confidence: 84,
      reason: `Filename match for ${model.filename}`,
      tags: ['missing', model.type]
    })),
    {
      id: 'hf-query-candidate',
      name: `${basis} search expansion`,
      source: 'HuggingFace',
      confidence: 67,
      reason: 'Fallback semantic query derived from workflow labels and missing model names.',
      tags: ['fallback', 'semantic']
    }
  ];
}

function sourceIcon(source: Candidate['source']) {
  if (source === 'Local') return Database;
  if (source === 'Civitai') return Sparkles;
  return Cloud;
}

export default function SearchWorkbenchVariant({
  models = fallbackModels,
  workflows = fallbackWorkflows,
  activityLog = []
}: VariantProps) {
  const [query, setQuery] = useState('');
  const [activeMode, setActiveMode] = useState('missing');
  const candidates = useMemo(() => buildCandidates(models, workflows, query), [models, workflows, query]);
  const missingModels = models.filter((model) => model.status === 'missing');
  const latestEvents = activityLog.slice(0, 4);

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
      <Card className="xl:sticky xl:top-4 xl:self-start">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSearch className="h-5 w-5 text-primary" />
            Search Workbench
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Turn workflow gaps into model discovery queries, candidates, and resolver notes.
          </p>
        </CardHeader>
        <CardContent className="space-y-5">
          <Tabs value={activeMode} onValueChange={setActiveMode}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="missing">Missing</TabsTrigger>
              <TabsTrigger value="url">URL</TabsTrigger>
              <TabsTrigger value="paste">Paste</TabsTrigger>
            </TabsList>
            <TabsContent value="missing" className="space-y-3">
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="mb-2 flex items-center gap-2 text-sm">
                  <Bot className="h-4 w-4" />
                  Resolver prompt seed
                </div>
                <p className="text-sm text-muted-foreground">
                  {missingModels[0]?.name || 'No missing model selected. Search a model, node pack, or workflow filename.'}
                </p>
              </div>
            </TabsContent>
            <TabsContent value="url" className="space-y-3">
              <div className="rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground">
                <Link2 className="mb-2 h-4 w-4" />
                Paste a Civitai, HuggingFace, GitHub, or workflow page URL to stage a resolver lookup.
              </div>
            </TabsContent>
            <TabsContent value="paste" className="space-y-3">
              <div className="rounded-lg border bg-muted/30 p-3 text-sm text-muted-foreground">
                <Upload className="mb-2 h-4 w-4" />
                Paste a missing-node traceback or workflow JSON snippet to extract dependency names.
              </div>
            </TabsContent>
          </Tabs>

          <div className="space-y-2">
            <label className="text-sm">Query</label>
            <div className="flex gap-2">
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="ip adapter plus sdxl, comfy node pack..."
              />
              <Button size="icon" aria-label="Search candidates">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border p-3">
              <div className="text-2xl">{missingModels.length}</div>
              <div className="text-xs text-muted-foreground">missing models</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-2xl">{workflows.filter((workflow) => workflow.status === 'missing-models').length}</div>
              <div className="text-xs text-muted-foreground">blocked workflows</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <History className="h-4 w-4" />
              Recent resolver activity
            </div>
            {(latestEvents.length > 0 ? latestEvents : [
              { id: 'extract', message: 'Extracted missing model names from workflow JSON.', timestamp: 'demo', type: 'import' as const },
              { id: 'fallback', message: 'Prepared HuggingFace fallback for uncertain filename match.', timestamp: 'demo', type: 'execution' as const }
            ]).map((event) => (
              <div key={event.id} className="rounded-md border bg-background p-2 text-xs">
                <div>{event.message}</div>
                <div className="mt-1 text-muted-foreground">{event.timestamp}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="flex items-center gap-2">
                <Wand2 className="h-5 w-5" />
                Candidate Board
              </CardTitle>
              <Button variant="outline" size="sm">
                <Filter className="mr-2 h-4 w-4" />
                Confidence first
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[520px] pr-4">
              <div className="grid gap-3 lg:grid-cols-2">
                {candidates.map((candidate) => {
                  const Icon = sourceIcon(candidate.source);
                  return (
                    <Card key={candidate.id} className="gap-0 overflow-hidden">
                      <div className="border-b bg-muted/30 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Icon className="h-4 w-4" />
                              {candidate.source}
                            </div>
                            <h3 className="mt-1 truncate">{candidate.name}</h3>
                          </div>
                          <Badge variant={candidate.confidence >= 85 ? 'default' : 'secondary'}>
                            {candidate.confidence}%
                          </Badge>
                        </div>
                      </div>
                      <div className="space-y-4 p-4">
                        <div>
                          <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
                            <span>Match confidence</span>
                            <span>{candidate.confidence}%</span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-muted">
                            <div className="h-full rounded-full bg-primary" style={{ width: `${candidate.confidence}%` }} />
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">{candidate.reason}</p>
                        <div className="flex flex-wrap gap-2">
                          {candidate.tags.map((tag) => (
                            <Badge key={tag} variant="outline">{tag}</Badge>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          <Button className="flex-1" size="sm">
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            Stage
                          </Button>
                          <Button className="flex-1" size="sm" variant="outline">
                            Details
                          </Button>
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="grid gap-4 p-4 md:grid-cols-3">
            {[
              { label: 'Extract', text: 'Parse workflow JSON and error logs.', icon: FileSearch },
              { label: 'Search', text: 'Fan out across local index, Civitai, and HuggingFace.', icon: Loader2 },
              { label: 'Verify', text: 'Compare filename, type, size, and workflow fit.', icon: CheckCircle2 }
            ].map((step) => {
              const Icon = step.icon;
              return (
                <div key={step.label} className="rounded-lg border p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${step.label === 'Search' ? 'animate-spin text-primary' : 'text-primary'}`} />
                    <span className="font-medium">{step.label}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{step.text}</p>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
