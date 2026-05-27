import { useState, useEffect, useCallback } from 'react';
import { Model, Workflow, Activity } from '../types';
import { comfyUIService, SearchFilters } from '../services/comfyui-service';

export interface UseComfyUIResult {
  models: Model[];
  workflows: Workflow[];
  activityLog: Activity[];
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Main hook for accessing ComfyUI data
 * Handles loading states, errors, and real-time updates
 */
export function useComfyUI(filters?: SearchFilters): UseComfyUIResult {
  const [models, setModels] = useState<Model[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [activityLog, setActivityLog] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [modelsData, workflowsData, activityData] = await Promise.all([
        comfyUIService.getModels(filters),
        comfyUIService.getWorkflows(filters),
        comfyUIService.getActivityLog(10)
      ]);

      setModels(modelsData);
      setWorkflows(workflowsData);
      setActivityLog(activityData);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch data'));
      console.error('Error fetching ComfyUI data:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();

    // Subscribe to real-time updates
    const unsubscribe = comfyUIService.subscribeToUpdates((event) => {
      if (event.type === 'refresh') {
        fetchData();
      } else if (event.type === 'model_updated') {
        setModels(prev => prev.map(m => m.id === event.data.id ? event.data : m));
      } else if (event.type === 'model_deleted') {
        setModels(prev => prev.filter(m => m.id !== event.data.id));
      } else if (event.type === 'activity') {
        setActivityLog(prev => [event.data, ...prev].slice(0, 10));
      }
    });

    return () => {
      unsubscribe();
    };
  }, [fetchData]);

  return {
    models,
    workflows,
    activityLog,
    loading,
    error,
    refetch: fetchData
  };
}
