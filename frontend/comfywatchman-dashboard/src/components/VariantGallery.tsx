import { useState } from 'react';
import type { ActivityLogItem, Model, Workflow } from '../types';
import OperatorConsoleVariant from './variants/OperatorConsoleVariant';
import QueueOpsVariant from './variants/QueueOpsVariant';
import GraphStudioVariant from './variants/GraphStudioVariant';
import SearchWorkbenchVariant from './variants/SearchWorkbenchVariant';
import ReadinessReviewVariant from './variants/ReadinessReviewVariant';
import {
  Blocks,
  CheckCircle2,
  Command,
  Download,
  GitBranch,
  GitPullRequest,
  ListChecks,
  Network,
  PackageSearch,
  PanelLeft,
  Sparkles,
} from 'lucide-react';

interface VariantGalleryProps {
  models: Model[];
  workflows: Workflow[];
  activityLog: ActivityLogItem[];
}

type VariantId =
  | 'operator'
  | 'queue'
  | 'graph'
  | 'search'
  | 'review'
  | 'pipeline';

const variantTabs: Array<{
  id: VariantId;
  label: string;
  source: string;
  icon: typeof Command;
}> = [
  { id: 'operator', label: 'Operator Console', source: 'ui-jules-control-room', icon: PanelLeft },
  { id: 'queue', label: 'Queue Ops', source: 'ui-automation-toolbox', icon: Download },
  { id: 'graph', label: 'Graph Studio', source: 'Uigraphnotes2 + style library', icon: Network },
  { id: 'search', label: 'Search Workbench', source: 'Uiwifeitemsearch', icon: PackageSearch },
  { id: 'review', label: 'Readiness Review', source: 'Comprehensive style library', icon: ListChecks },
  { id: 'pipeline', label: 'Pipeline Board', source: 'ui-claude-parallel', icon: GitPullRequest },
];

function getModelTotals(models: Model[]) {
  const missing = models.filter((model) => model.status === 'missing');
  return { missing };
}

function PipelineBoardVariant({ models, workflows }: VariantGalleryProps) {
  const { missing } = getModelTotals(models);
  const columns = [
    {
      title: 'Intake',
      icon: GitBranch,
      cards: workflows.slice(0, 3).map((workflow) => ({
        title: workflow.name,
        body: 'New workflow awaiting dependency inspection',
        meta: workflow.filename,
      })),
    },
    {
      title: 'Resolving',
      icon: Sparkles,
      cards: missing.slice(0, 3).map((model) => ({
        title: model.name,
        body: `${model.type} lookup needs confidence review`,
        meta: model.size,
      })),
    },
    {
      title: 'Approval',
      icon: ListChecks,
      cards: [
        {
          title: 'Download plan',
          body: 'Operator approval before writing into model folders',
          meta: `${missing.length} targets`,
        },
      ],
    },
    {
      title: 'Ready',
      icon: CheckCircle2,
      cards: workflows
        .filter((workflow) => workflow.status === 'ready')
        .slice(0, 3)
        .map((workflow) => ({
          title: workflow.name,
          body: 'Runnable with current local inventory',
          meta: `${workflow.usageCount || 0} runs`,
        })),
    },
  ];

  return (
    <section className="cw-variant cw-board">
      {columns.map((column) => {
        const Icon = column.icon;
        return (
          <div className="cw-board-column" key={column.title}>
            <div className="cw-board-title">
              <Icon size={18} />
              <h3>{column.title}</h3>
              <span>{column.cards.length}</span>
            </div>
            <div className="cw-board-cards">
              {column.cards.map((card) => (
                <article key={`${column.title}-${card.title}`} className="cw-board-card">
                  <strong>{card.title}</strong>
                  <p>{card.body}</p>
                  <small>{card.meta}</small>
                </article>
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}

export function VariantGallery({ models, workflows, activityLog }: VariantGalleryProps) {
  const [activeVariant, setActiveVariant] = useState<VariantId>('operator');
  const active = variantTabs.find((variant) => variant.id === activeVariant) || variantTabs[0];

  return (
    <div className="cw-gallery">
      <header className="cw-gallery-header">
        <div>
          <p className="cw-kicker">Donor UI ports</p>
          <h1>ComfyWatchman interface variants</h1>
          <span>Purpose-shifted from the original `big-ui` examples into Comfy model, workflow, and readiness surfaces.</span>
        </div>
        <div className="cw-source-badge">
          <Blocks size={16} />
          <span>{active.source}</span>
        </div>
      </header>

      <nav className="cw-variant-nav" aria-label="UI variants">
        {variantTabs.map((variant) => {
          const Icon = variant.icon;
          return (
            <button
              key={variant.id}
              type="button"
              className={variant.id === activeVariant ? 'is-active' : ''}
              onClick={() => setActiveVariant(variant.id)}
            >
              <Icon size={16} />
              <span>{variant.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="cw-port-frame">
        {activeVariant === 'operator' && <OperatorConsoleVariant />}
        {activeVariant === 'queue' && <QueueOpsVariant />}
        {activeVariant === 'graph' && <GraphStudioVariant />}
        {activeVariant === 'search' && <SearchWorkbenchVariant />}
        {activeVariant === 'review' && <ReadinessReviewVariant />}
        {activeVariant === 'pipeline' && (
          <PipelineBoardVariant models={models} workflows={workflows} activityLog={activityLog} />
        )}
      </div>
    </div>
  );
}
