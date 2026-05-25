import { useState } from 'react';
import { Model } from '../types';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import {
  FileBox,
  HardDrive,
  Layers,
  Network,
  Wand2,
  Download,
  Star,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Button } from './ui/button';

interface ModelCardProps {
  model: Model;
  workflows: Array<{ id: string; name: string }>;
}

const modelIcons = {
  Checkpoint: FileBox,
  LORA: Wand2,
  VAE: Layers,
  CLIP: Network,
  UNET: Network,
  ControlNet: Network,
  Upscale: HardDrive,
  Other: FileBox
};

export function ModelCard({ model, workflows }: ModelCardProps) {
  const [expanded, setExpanded] = useState(false);
  const Icon = modelIcons[model.type];

  const associatedWorkflowNames = workflows
    .filter(w => model.associatedWorkflows.includes(w.id))
    .map(w => w.name);

  return (
    <Card className="overflow-hidden hover:border-primary/50 transition-colors">
      <div
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${model.status === 'available' ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
            <Icon className={`w-5 h-5 ${model.status === 'available' ? 'text-green-500' : 'text-red-500'}`} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h3 className="truncate">{model.name}</h3>
                <p className="text-sm text-muted-foreground truncate mt-1">
                  {model.filename}
                </p>
              </div>
              {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
            </div>

            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <Badge variant={model.status === 'available' ? 'default' : 'destructive'}>
                {model.type}
              </Badge>
              <span className="text-xs text-muted-foreground">{model.size}</span>
              {model.rating && (
                <div className="flex items-center gap-1">
                  <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                  <span className="text-xs">{model.rating}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-border p-4 bg-muted/20">
          <div className="space-y-4">
            {model.previewImages && model.previewImages.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm">Preview</h4>
                <div className="grid grid-cols-3 gap-2">
                  {model.previewImages.map((img, idx) => (
                    <img
                      key={idx}
                      src={img}
                      alt={`Preview ${idx + 1}`}
                      className="w-full h-24 object-cover rounded"
                    />
                  ))}
                </div>
              </div>
            )}

            {model.metadata && (
              <div>
                <h4 className="mb-2 text-sm">Metadata</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  {model.metadata.description && (
                    <p>{model.metadata.description}</p>
                  )}
                  {model.metadata.baseModel && (
                    <p>Base Model: {model.metadata.baseModel}</p>
                  )}
                  {model.metadata.version && (
                    <p>Version: {model.metadata.version}</p>
                  )}
                  {model.metadata.triggerWords && (
                    <p>Trigger Words: {model.metadata.triggerWords.join(', ')}</p>
                  )}
                </div>
              </div>
            )}

            <div>
              <h4 className="mb-2 text-sm">Details</h4>
              <div className="space-y-1 text-sm text-muted-foreground">
                <p>Path: {model.path}</p>
                <p>Date Added: {model.dateAdded}</p>
                {model.usageCount !== undefined && (
                  <p>Used {model.usageCount} times</p>
                )}
              </div>
            </div>

            {associatedWorkflowNames.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm">Used in Workflows</h4>
                <div className="flex flex-wrap gap-1">
                  {associatedWorkflowNames.map((name, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {model.status === 'missing' && (
              <Button className="w-full" variant="default">
                <Download className="w-4 h-4 mr-2" />
                Download Model
              </Button>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
