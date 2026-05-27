export type ModelType =
  | 'Checkpoint'
  | 'LORA'
  | 'VAE'
  | 'CLIP'
  | 'UNET'
  | 'ControlNet'
  | 'Upscale'
  | 'Other';

export interface Model {
  id: string;
  name: string;
  filename: string;
  type: ModelType;
  size: string;
  sizeBytes: number;
  dateAdded: string;
  status: 'available' | 'missing';
  path: string;
  metadata?: {
    description?: string;
    triggerWords?: string[];
    baseModel?: string;
    version?: string;
  };
  previewImages?: string[];
  associatedWorkflows: string[];
  rating?: number;
  usageCount?: number;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  filename: string;
  createdDate: string;
  lastRun?: string;
  status: 'ready' | 'missing-models';
  requiredModels: {
    modelId: string;
    modelName: string;
    available: boolean;
  }[];
  previewImage?: string;
  category?: string[];
  rating?: number;
  usageCount?: number;
}

export interface ActivityLogItem {
  id: string;
  type: 'download' | 'execution' | 'error' | 'import';
  message: string;
  timestamp: string;
}

// ComfyWatchman: Agentic Search Types
export type SearchBackend = 'API' | 'Web' | 'HuggingFace';

export type SearchPhase = 'initial' | 'fallback' | 'doubt_resolution' | 'complete' | 'failed';

export type SearchConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNCERTAIN';

export interface SearchCandidate {
  id: string;
  modelName: string;
  source: SearchBackend;
  downloadUrl?: string;
  confidence: SearchConfidence;
  confidenceScore: number; // 0-100
  reasoning: string;
  metadata?: {
    size?: string;
    version?: string;
    author?: string;
    tags?: string[];
    downloads?: number;
    rating?: number;
  };
  verificationStatus?: 'pending' | 'verified' | 'failed';
}

export interface SearchStep {
  id: string;
  phase: SearchPhase;
  backend: SearchBackend;
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  timestamp: string;
  duration?: number;
  message: string;
  candidatesFound?: number;
  error?: string;
}

export interface SearchRun {
  id: string;
  query: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  currentPhase: SearchPhase;
  currentBackend?: SearchBackend;
  startTime?: string;
  endTime?: string;
  duration?: number;
  steps: SearchStep[];
  candidates: SearchCandidate[];
  selectedCandidate?: SearchCandidate;
  strategy: SearchBackend[];
  retryCount: number;
  logs: SearchLogEntry[];
}

export interface SearchLogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  details?: any;
}

export interface SearchStrategy {
  name: string;
  backends: SearchBackend[];
  description: string;
}
