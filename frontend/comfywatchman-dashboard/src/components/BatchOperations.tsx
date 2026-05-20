import { useState } from 'react';
import { Model } from '../types';
import { Checkbox } from './ui/checkbox';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import {
  Trash2,
  Download,
  Tag,
  FolderOpen,
  CheckSquare,
  XSquare
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './ui/dropdown-menu';
import { toast } from 'sonner';

interface BatchOperationsProps {
  models: Model[];
}

export function BatchOperations({ models }: BatchOperationsProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const handleToggle = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(models.map(m => m.id)));
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleBulkAction = (action: string) => {
    const count = selectedIds.size;
    toast.success(`${action} applied to ${count} model${count !== 1 ? 's' : ''}`);
    setSelectedIds(new Set());
  };

  const selectedModels = models.filter(m => selectedIds.has(m.id));
  const totalSize = selectedModels.reduce((sum, m) => sum + m.sizeBytes, 0);
  const formattedSize = (totalSize / (1024 ** 3)).toFixed(2) + ' GB';

  return (
    <div className="space-y-4">
      {/* Batch Action Toolbar */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h3>Batch Operations</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {selectedIds.size > 0
                  ? `${selectedIds.size} item${selectedIds.size !== 1 ? 's' : ''} selected (${formattedSize})`
                  : 'Select items to perform bulk actions'
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
            >
              <CheckSquare className="w-4 h-4 mr-2" />
              Select All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDeselectAll}
              disabled={selectedIds.size === 0}
            >
              <XSquare className="w-4 h-4 mr-2" />
              Deselect All
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  size="sm"
                  disabled={selectedIds.size === 0}
                >
                  Actions ({selectedIds.size})
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleBulkAction('Download')}>
                  <Download className="w-4 h-4 mr-2" />
                  Download Selected
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleBulkAction('Add Tags')}>
                  <Tag className="w-4 h-4 mr-2" />
                  Add Tags
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleBulkAction('Move to Folder')}>
                  <FolderOpen className="w-4 h-4 mr-2" />
                  Move to Folder
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => handleBulkAction('Delete')}
                  className="text-red-500"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Selected
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </Card>

      {/* Model List */}
      <div className="grid gap-3">
        {models.map((model) => (
          <Card
            key={model.id}
            className={`p-4 transition-colors ${
              selectedIds.has(model.id) ? 'bg-primary/5 border-primary' : ''
            }`}
          >
            <div className="flex items-center gap-4">
              <Checkbox
                checked={selectedIds.has(model.id)}
                onCheckedChange={() => handleToggle(model.id)}
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="truncate">{model.name}</h4>
                  <Badge variant="secondary">{model.type}</Badge>
                  {model.status === 'missing' && (
                    <Badge variant="destructive">Missing</Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground truncate">
                  {model.filename}
                </p>
              </div>

              <div className="text-sm text-muted-foreground">
                {model.size}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
