import { Card } from './ui/card';
import { Model, Workflow } from '../types';
import { Network } from 'lucide-react';

interface DependencyGraphProps {
  models: Model[];
  workflows: Workflow[];
}

export function DependencyGraph({ models, workflows }: DependencyGraphProps) {
  // Create a simple visualization showing connections
  const topModels = models
    .filter(m => m.associatedWorkflows.length > 0)
    .sort((a, b) => b.associatedWorkflows.length - a.associatedWorkflows.length)
    .slice(0, 6);

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <Network className="w-5 h-5" />
        <h3>Dependency Overview</h3>
      </div>

      <div className="space-y-4">
        {topModels.map((model) => {
          const connectedWorkflows = workflows.filter(w =>
            model.associatedWorkflows.includes(w.id)
          );

          return (
            <div key={model.id} className="space-y-2">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${model.status === 'available' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm">{model.name}</span>
              </div>
              <div className="ml-4 pl-4 border-l-2 border-border space-y-1">
                {connectedWorkflows.map((workflow) => (
                  <div key={workflow.id} className="text-xs text-muted-foreground flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary/50" />
                    {workflow.name}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-border text-xs text-muted-foreground">
        Showing top {topModels.length} most connected models
      </div>
    </Card>
  );
}
