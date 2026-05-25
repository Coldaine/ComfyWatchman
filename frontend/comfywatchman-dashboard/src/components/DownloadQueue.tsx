import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import {
  Play,
  Pause,
  X,
  MoveUp,
  MoveDown,
  Download,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

interface QueueItem {
  id: string;
  name: string;
  size: string;
  sizeBytes: number;
  progress: number;
  status: 'pending' | 'downloading' | 'paused' | 'completed' | 'error';
  speed?: string;
  eta?: string;
}

export function DownloadQueue() {
  const [queue, setQueue] = useState<QueueItem[]>([
    {
      id: '1',
      name: 'Realistic Vision V6.0',
      size: '5.21 GB',
      sizeBytes: 5210000000,
      progress: 47,
      status: 'downloading',
      speed: '12.3 MB/s',
      eta: '5m 23s'
    },
    {
      id: '2',
      name: 'DreamShaper XL',
      size: '6.94 GB',
      sizeBytes: 6940000000,
      progress: 0,
      status: 'pending'
    },
    {
      id: '3',
      name: 'ControlNet Depth',
      size: '1.45 GB',
      sizeBytes: 1450000000,
      progress: 100,
      status: 'completed'
    },
    {
      id: '4',
      name: 'VAE ft MSE',
      size: '335 MB',
      sizeBytes: 335000000,
      progress: 23,
      status: 'paused'
    },
    {
      id: '5',
      name: 'SDXL Base 1.0',
      size: '6.46 GB',
      sizeBytes: 6460000000,
      progress: 15,
      status: 'error'
    },
  ]);

  // Simulate download progress
  useEffect(() => {
    const interval = setInterval(() => {
      setQueue(prevQueue =>
        prevQueue.map(item => {
          if (item.status === 'downloading' && item.progress < 100) {
            const newProgress = Math.min(item.progress + Math.random() * 3, 100);
            return {
              ...item,
              progress: newProgress,
              status: newProgress >= 100 ? 'completed' : 'downloading'
            };
          }
          return item;
        })
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handlePauseResume = (id: string) => {
    setQueue(prevQueue =>
      prevQueue.map(item => {
        if (item.id === id) {
          const newStatus = item.status === 'paused' ? 'downloading' : 'paused';
          toast.success(newStatus === 'paused' ? 'Download paused' : 'Download resumed');
          return { ...item, status: newStatus };
        }
        return item;
      })
    );
  };

  const handleRemove = (id: string) => {
    setQueue(prevQueue => prevQueue.filter(item => item.id !== id));
    toast.success('Removed from queue');
  };

  const handleRetry = (id: string) => {
    setQueue(prevQueue =>
      prevQueue.map(item => {
        if (item.id === id) {
          toast.success('Retrying download');
          return { ...item, status: 'downloading', progress: 0 };
        }
        return item;
      })
    );
  };

  const handlePriority = (id: string, direction: 'up' | 'down') => {
    setQueue(prevQueue => {
      const index = prevQueue.findIndex(item => item.id === id);
      if (
        (direction === 'up' && index === 0) ||
        (direction === 'down' && index === prevQueue.length - 1)
      ) {
        return prevQueue;
      }

      const newQueue = [...prevQueue];
      const swapIndex = direction === 'up' ? index - 1 : index + 1;
      [newQueue[index], newQueue[swapIndex]] = [newQueue[swapIndex], newQueue[index]];

      toast.success('Priority updated');
      return newQueue;
    });
  };

  const stats = {
    total: queue.length,
    downloading: queue.filter(q => q.status === 'downloading').length,
    pending: queue.filter(q => q.status === 'pending').length,
    completed: queue.filter(q => q.status === 'completed').length,
    paused: queue.filter(q => q.status === 'paused').length,
    errors: queue.filter(q => q.status === 'error').length,
  };

  const getStatusColor = (status: QueueItem['status']) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'downloading': return 'text-blue-500';
      case 'paused': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-muted-foreground';
    }
  };

  return (
    <div className="space-y-4">
      {/* Stats Overview */}
      <div className="grid grid-cols-6 gap-4">
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Total</div>
          <div className="text-2xl mt-1">{stats.total}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-blue-500">Downloading</div>
          <div className="text-2xl mt-1">{stats.downloading}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-muted-foreground">Pending</div>
          <div className="text-2xl mt-1">{stats.pending}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-yellow-500">Paused</div>
          <div className="text-2xl mt-1">{stats.paused}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-green-500">Completed</div>
          <div className="text-2xl mt-1">{stats.completed}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-red-500">Errors</div>
          <div className="text-2xl mt-1">{stats.errors}</div>
        </Card>
      </div>

      {/* Queue Header */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <h3>Download Queue</h3>
          <div className="flex gap-2">
            <Button size="sm" variant="outline">
              <Pause className="w-4 h-4 mr-2" />
              Pause All
            </Button>
            <Button size="sm" variant="outline">
              <Play className="w-4 h-4 mr-2" />
              Resume All
            </Button>
            <Button size="sm">
              <Download className="w-4 h-4 mr-2" />
              Add to Queue
            </Button>
          </div>
        </div>
      </Card>

      {/* Queue Items */}
      <div className="space-y-3">
        {queue.map((item, index) => (
          <Card key={item.id} className="p-4">
            <div className="space-y-3">
              {/* Header Row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {item.status === 'completed' && (
                    <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                  )}
                  {item.status === 'error' && (
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  )}
                  {item.status === 'downloading' && (
                    <Download className="w-5 h-5 text-blue-500 animate-pulse flex-shrink-0" />
                  )}
                  {item.status === 'pending' && (
                    <Download className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  )}
                  {item.status === 'paused' && (
                    <Pause className="w-5 h-5 text-yellow-500 flex-shrink-0" />
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="truncate">{item.name}</h4>
                      <Badge variant="outline">{item.size}</Badge>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                      <span className={getStatusColor(item.status)}>
                        {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                      </span>
                      {item.speed && <span>{item.speed}</span>}
                      {item.eta && <span>ETA: {item.eta}</span>}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Priority Controls */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handlePriority(item.id, 'up')}
                    disabled={index === 0}
                  >
                    <MoveUp className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handlePriority(item.id, 'down')}
                    disabled={index === queue.length - 1}
                  >
                    <MoveDown className="w-4 h-4" />
                  </Button>

                  {/* Action Buttons */}
                  {item.status === 'error' ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRetry(item.id)}
                    >
                      Retry
                    </Button>
                  ) : item.status !== 'completed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePauseResume(item.id)}
                    >
                      {item.status === 'paused' ? (
                        <Play className="w-4 h-4" />
                      ) : (
                        <Pause className="w-4 h-4" />
                      )}
                    </Button>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemove(item.id)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Progress Bar */}
              {item.status !== 'pending' && (
                <div className="space-y-1">
                  <Progress value={item.progress} />
                  <div className="text-xs text-muted-foreground text-right">
                    {item.progress.toFixed(1)}%
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
