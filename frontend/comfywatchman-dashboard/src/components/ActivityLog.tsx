import { Card } from './ui/card';
import { ActivityLogItem } from '../types';
import { Download, Play, AlertCircle, FileInput, Clock } from 'lucide-react';

interface ActivityLogProps {
  activities: ActivityLogItem[];
}

const activityIcons = {
  download: Download,
  execution: Play,
  error: AlertCircle,
  import: FileInput
};

const activityColors = {
  download: 'text-blue-500',
  execution: 'text-green-500',
  error: 'text-red-500',
  import: 'text-purple-500'
};

export function ActivityLog({ activities }: ActivityLogProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = Math.max(0, now.getTime() - date.getTime());
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-5 h-5" />
        <h3>Recent Activity</h3>
      </div>

      <div className="space-y-3">
        {activities.map((activity) => {
          const Icon = activityIcons[activity.type];
          const colorClass = activityColors[activity.type];

          return (
            <div key={activity.id} className="flex items-start gap-3">
              <div className={`p-1.5 rounded ${colorClass} bg-current/10 flex-shrink-0`}>
                <Icon className={`w-4 h-4 ${colorClass}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm">{activity.message}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatTime(activity.timestamp)}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
