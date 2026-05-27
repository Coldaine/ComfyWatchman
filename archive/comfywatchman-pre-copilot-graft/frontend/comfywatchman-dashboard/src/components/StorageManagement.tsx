import { Card } from './ui/card';
import { Model } from '../types';
import { HardDrive, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';

interface StorageManagementProps {
  models: Model[];
}

export function StorageManagement({ models }: StorageManagementProps) {
  const totalStorage = models.reduce((acc, model) => acc + model.sizeBytes, 0);
  const totalGB = (totalStorage / 1024 / 1024 / 1024).toFixed(2);

  const storageByType = models.reduce((acc, model) => {
    if (!acc[model.type]) {
      acc[model.type] = { count: 0, bytes: 0 };
    }
    acc[model.type].count += 1;
    acc[model.type].bytes += model.sizeBytes;
    return acc;
  }, {} as Record<string, { count: number; bytes: number }>);

  const sortedTypes = Object.entries(storageByType)
    .sort((a, b) => b[1].bytes - a[1].bytes)
    .slice(0, 5);

  const maxBytes = Math.max(...sortedTypes.map(([, data]) => data.bytes));

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <HardDrive className="w-5 h-5" />
          <h3>Storage Usage</h3>
        </div>
        <div className="text-sm text-muted-foreground">
          Total: {totalGB} GB
        </div>
      </div>

      <div className="space-y-4">
        {sortedTypes.map(([type, data]) => {
          const gb = (data.bytes / 1024 / 1024 / 1024).toFixed(2);
          const percentage = (data.bytes / maxBytes) * 100;

          return (
            <div key={type} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>{type}</span>
                <span className="text-muted-foreground">
                  {gb} GB ({data.count} files)
                </span>
              </div>
              <Progress value={percentage} className="h-2" />
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-border">
        <Button variant="outline" className="w-full" size="sm">
          <Trash2 className="w-4 h-4 mr-2" />
          Clean Up Unused Models
        </Button>
      </div>
    </Card>
  );
}
