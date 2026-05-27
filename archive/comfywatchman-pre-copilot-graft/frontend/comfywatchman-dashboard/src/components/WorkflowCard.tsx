import { useState } from 'react';
import { Workflow } from '../types';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { Button } from './ui/button';
import {
  CheckCircle2,
  XCircle,
  Download,
  Play,
  Star,
  ChevronDown,
  ChevronUp,
  Calendar,
  Clock
} from 'lucide-react';

interface WorkflowCardProps {
  workflow: Workflow;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const [expanded, setExpanded] = useState(false);

  const missingModelsCount = workflow.requiredModels.filter(m => !m.available).length;
  const isReady = workflow.status === 'ready';

  return (
    <Card className="overflow-hidden hover:border-primary/50 transition-colors">
      <button
        type="button"
        className="block w-full p-4 text-left"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${isReady ? 'bg-green-500/10' : 'bg-red-500/10'} flex-shrink-0`}>
            {isReady ? (
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            ) : (
              <XCircle className="w-5 h-5 text-red-500" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h3 className="truncate">{workflow.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  {workflow.description}
                </p>
              </div>
              {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
            </div>

            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <Badge variant={isReady ? 'default' : 'destructive'}>
                {isReady ? 'Ready' : `${missingModelsCount} Missing`}
              </Badge>
              {workflow.category && workflow.category.map((cat, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {cat}
                </Badge>
              ))}
              {workflow.rating && (
                <div className="flex items-center gap-1">
                  <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                  <span className="text-xs">{workflow.rating}</span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {workflow.createdDate}
              </div>
              {workflow.lastRun && (
                <div className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Last run: {workflow.lastRun}
                </div>
              )}
            </div>
          </div>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border p-4 bg-muted/20">
          <div className="space-y-4">
            {workflow.previewImage && (
              <div>
                <h4 className="mb-2 text-sm">Preview</h4>
                <img
                  src={workflow.previewImage}
                  alt={workflow.name}
                  className="w-full h-48 object-cover rounded"
                />
              </div>
            )}

            <div>
              <h4 className="mb-2 text-sm">Required Models ({workflow.requiredModels.length})</h4>
              <div className="space-y-2">
                {workflow.requiredModels.map((model, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded bg-background border border-border"
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {model.available ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                      )}
                      <span className="text-sm truncate">{model.modelName}</span>
                    </div>
                    {!model.available && (
                      <Button size="sm" variant="ghost" className="flex-shrink-0">
                        <Download className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-sm">Details</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <p>Filename: {workflow.filename}</p>
                {workflow.usageCount !== undefined && (
                  <p>Executed {workflow.usageCount} times</p>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              {isReady && (
                <Button className="flex-1">
                  <Play className="w-4 h-4 mr-2" />
                  Run Workflow
                </Button>
              )}
              {!isReady && (
                <Button className="flex-1" variant="default">
                  <Download className="w-4 h-4 mr-2" />
                  Download Missing Models
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
