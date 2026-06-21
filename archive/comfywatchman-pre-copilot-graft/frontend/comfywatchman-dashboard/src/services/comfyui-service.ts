import { Model, Workflow, Activity, ModelType } from '../types';
import { mockModels, mockWorkflows, mockActivityLog } from '../data/mockData';

export interface StorageStats {
  totalSize: number;
  totalSizeBytes: number;
  byType: Record<string, { size: string; sizeBytes: number; count: number }>;
  largestModels: Array<{ name: string; size: string; sizeBytes: number }>;
}

export interface DownloadProgress {
  id: string;
  modelId: string;
  modelName: string;
  progress: number;
  speed: string;
  status: 'queued' | 'downloading' | 'paused' | 'complete' | 'error';
  error?: string;
}

export interface SearchFilters {
  query?: string;
  type?: ModelType | 'all';
  status?: 'available' | 'missing' | 'downloading' | 'all';
  tags?: string[];
}

export interface SortConfig {
  field: 'name' | 'size' | 'date' | 'usage';
  direction: 'asc' | 'desc';
}

type UpdateCallback = (event: UpdateEvent) => void;

export interface UpdateEvent {
  type: 'model_added' | 'model_updated' | 'model_deleted' | 'download_progress' | 'activity' | 'refresh';
  data: any;
}

/**
 * ComfyUI Service - Data layer abstraction
 *
 * This is currently a mock implementation, but provides the interface
 * for real backend integration. Replace methods with actual API calls
 * or filesystem operations as needed.
 */
export class ComfyUIService {
  private updateCallbacks: Set<UpdateCallback> = new Set();
  private pollingInterval?: number;
  private simulateRealTime: boolean;

  constructor(simulateRealTime: boolean = false) {
    this.simulateRealTime = simulateRealTime;

    if (simulateRealTime) {
      this.startRealtimeSimulation();
    }
  }

  // ============================================================================
  // Models
  // ============================================================================

  async getModels(filters?: SearchFilters): Promise<Model[]> {
    // Simulate network delay
    await this.delay(100);

    let models = [...mockModels];

    if (filters) {
      if (filters.query) {
        const query = filters.query.toLowerCase();
        models = models.filter(m =>
          m.name.toLowerCase().includes(query) ||
          m.filename.toLowerCase().includes(query) ||
          m.tags?.some(t => t.toLowerCase().includes(query))
        );
      }

      if (filters.type && filters.type !== 'all') {
        models = models.filter(m => m.type === filters.type);
      }

      if (filters.status && filters.status !== 'all') {
        models = models.filter(m => m.status === filters.status);
      }

      if (filters.tags && filters.tags.length > 0) {
        models = models.filter(m =>
          filters.tags!.some(tag => m.tags?.includes(tag))
        );
      }
    }

    return models;
  }

  async getModel(id: string): Promise<Model | null> {
    await this.delay(50);
    return mockModels.find(m => m.id === id) || null;
  }

  async updateModel(id: string, updates: Partial<Model>): Promise<Model> {
    await this.delay(100);

    // In real implementation, update model in database/filesystem
    const model = mockModels.find(m => m.id === id);
    if (!model) throw new Error('Model not found');

    const updated = { ...model, ...updates };
    this.notifyUpdate({ type: 'model_updated', data: updated });

    return updated;
  }

  async deleteModel(id: string): Promise<void> {
    await this.delay(100);

    // In real implementation, delete model file and update database
    this.notifyUpdate({ type: 'model_deleted', data: { id } });
  }

  async batchDownload(modelIds: string[]): Promise<void> {
    await this.delay(200);

    // In real implementation, queue downloads
    console.log('Batch downloading:', modelIds);
  }

  async batchDelete(modelIds: string[]): Promise<void> {
    await this.delay(200);

    // In real implementation, delete multiple models
    console.log('Batch deleting:', modelIds);
  }

  async batchAddTags(modelIds: string[], tags: string[]): Promise<void> {
    await this.delay(150);

    // In real implementation, update model metadata
    console.log('Adding tags to models:', modelIds, tags);
  }

  // ============================================================================
  // Workflows
  // ============================================================================

  async getWorkflows(filters?: SearchFilters): Promise<Workflow[]> {
    await this.delay(100);

    let workflows = [...mockWorkflows];

    if (filters?.query) {
      const query = filters.query.toLowerCase();
      workflows = workflows.filter(w =>
        w.name.toLowerCase().includes(query) ||
        w.description.toLowerCase().includes(query) ||
        w.tags?.some(t => t.toLowerCase().includes(query))
      );
    }

    return workflows;
  }

  async getWorkflow(id: string): Promise<Workflow | null> {
    await this.delay(50);
    return mockWorkflows.find(w => w.id === id) || null;
  }

  async updateWorkflow(id: string, updates: Partial<Workflow>): Promise<Workflow> {
    await this.delay(100);

    const workflow = mockWorkflows.find(w => w.id === id);
    if (!workflow) throw new Error('Workflow not found');

    return { ...workflow, ...updates };
  }

  async saveWorkflowOrder(orderedIds: string[]): Promise<void> {
    await this.delay(100);

    // In real implementation, save to config file or database
    console.log('Saving workflow order:', orderedIds);
  }

  // ============================================================================
  // Storage & Analytics
  // ============================================================================

  async getStorageStats(): Promise<StorageStats> {
    await this.delay(100);

    const models = mockModels;
    const totalSizeBytes = models.reduce((sum, m) => sum + m.sizeBytes, 0);

    const byType: Record<string, { size: string; sizeBytes: number; count: number }> = {};

    models.forEach(model => {
      if (!byType[model.type]) {
        byType[model.type] = { size: '0 GB', sizeBytes: 0, count: 0 };
      }
      byType[model.type].sizeBytes += model.sizeBytes;
      byType[model.type].count += 1;
    });

    Object.keys(byType).forEach(type => {
      byType[type].size = this.formatBytes(byType[type].sizeBytes);
    });

    const largestModels = [...models]
      .sort((a, b) => b.sizeBytes - a.sizeBytes)
      .slice(0, 5)
      .map(m => ({ name: m.name, size: m.size, sizeBytes: m.sizeBytes }));

    return {
      totalSize: this.formatBytes(totalSizeBytes),
      totalSizeBytes,
      byType,
      largestModels
    };
  }

  // ============================================================================
  // Activity Log
  // ============================================================================

  async getActivityLog(limit: number = 10): Promise<Activity[]> {
    await this.delay(50);
    return mockActivityLog.slice(0, limit);
  }

  async logActivity(activity: Omit<Activity, 'id' | 'timestamp'>): Promise<void> {
    await this.delay(50);

    const newActivity: Activity = {
      id: `activity-${Date.now()}`,
      timestamp: new Date().toISOString(),
      ...activity
    };

    this.notifyUpdate({ type: 'activity', data: newActivity });
  }

  // ============================================================================
  // Downloads
  // ============================================================================

  async startDownload(modelId: string): Promise<string> {
    await this.delay(100);

    const downloadId = `download-${Date.now()}-${modelId}`;

    // In real implementation, start actual download
    console.log('Starting download:', downloadId);

    return downloadId;
  }

  async pauseDownload(downloadId: string): Promise<void> {
    await this.delay(50);
    console.log('Pausing download:', downloadId);
  }

  async resumeDownload(downloadId: string): Promise<void> {
    await this.delay(50);
    console.log('Resuming download:', downloadId);
  }

  async cancelDownload(downloadId: string): Promise<void> {
    await this.delay(50);
    console.log('Cancelling download:', downloadId);
  }

  // ============================================================================
  // Export/Import
  // ============================================================================

  async exportData(type: 'models' | 'workflows' | 'all'): Promise<string> {
    await this.delay(200);

    const data: any = { exportDate: new Date().toISOString() };

    if (type === 'models' || type === 'all') {
      data.models = mockModels;
    }

    if (type === 'workflows' || type === 'all') {
      data.workflows = mockWorkflows;
    }

    return JSON.stringify(data, null, 2);
  }

  async importData(jsonData: string): Promise<{ models: number; workflows: number }> {
    await this.delay(300);

    const data = JSON.parse(jsonData);
    let importedModels = 0;
    let importedWorkflows = 0;

    if (Array.isArray(data.models)) {
      for (const model of data.models as Model[]) {
        if (!model?.id || mockModels.some(existing => existing.id === model.id)) {
          continue;
        }
        mockModels.push(model);
        importedModels += 1;
      }
    }

    if (Array.isArray(data.workflows)) {
      for (const workflow of data.workflows as Workflow[]) {
        if (!workflow?.id || mockWorkflows.some(existing => existing.id === workflow.id)) {
          continue;
        }
        mockWorkflows.push(workflow);
        importedWorkflows += 1;
      }
    }

    this.notifyUpdate({ type: 'refresh', data: null });

    return {
      models: importedModels,
      workflows: importedWorkflows
    };
  }

  // ============================================================================
  // Real-time Updates
  // ============================================================================

  subscribeToUpdates(callback: UpdateCallback): () => void {
    this.updateCallbacks.add(callback);

    return () => {
      this.updateCallbacks.delete(callback);
    };
  }

  private notifyUpdate(event: UpdateEvent): void {
    this.updateCallbacks.forEach(callback => {
      try {
        callback(event);
      } catch (error) {
        console.error('Error in update callback:', error);
      }
    });
  }

  private startRealtimeSimulation(): void {
    // Simulate periodic updates for demo purposes
    this.pollingInterval = window.setInterval(() => {
      // Randomly trigger activity updates
      if (Math.random() > 0.7) {
        const activities = [
          { type: 'model_scan' as const, description: 'Model scan completed', status: 'success' as const },
          { type: 'download' as const, description: 'Download in progress', status: 'info' as const },
        ];

        const activity = activities[Math.floor(Math.random() * activities.length)];
        this.logActivity(activity);
      }
    }, 10000); // Every 10 seconds
  }

  destroy(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    this.updateCallbacks.clear();
  }

  // ============================================================================
  // Utilities
  // ============================================================================

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// Singleton instance for the app
export const comfyUIService = new ComfyUIService(false);
