import {
  SearchRun,
  SearchCandidate,
  SearchStep,
  SearchLogEntry,
  SearchBackend,
  SearchPhase,
  SearchConfidence
} from '../types';

// Mock service for Agentic Search operations
// In production, this would connect to the ComfyWatchman backend

let currentRunId = 0;
let logId = 0;

function generateId(): string {
  return `run-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function generateLogId(): string {
  return `log-${logId++}`;
}

// Simulate search delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Generate mock search results
function generateMockCandidates(
  query: string,
  backend: SearchBackend,
  count: number = 3
): SearchCandidate[] {
  const confidenceLevels: SearchConfidence[] = ['HIGH', 'MEDIUM', 'LOW', 'UNCERTAIN'];
  const confidenceScores: Record<SearchConfidence, [number, number]> = {
    HIGH: [85, 100],
    MEDIUM: [60, 84],
    LOW: [40, 59],
    UNCERTAIN: [0, 39],
  };

  return Array.from({ length: count }, (_, i) => {
    const confidence = confidenceLevels[Math.min(i, confidenceLevels.length - 1)];
    const [min, max] = confidenceScores[confidence];
    const score = Math.floor(Math.random() * (max - min + 1)) + min;

    return {
      id: `candidate-${Date.now()}-${i}`,
      modelName: `${query}_${backend.toLowerCase()}_v${i + 1}`,
      source: backend,
      downloadUrl: `https://example.com/models/${query}_${i + 1}.safetensors`,
      confidence,
      confidenceScore: score,
      reasoning: generateReasoning(query, backend, confidence, i),
      metadata: {
        size: `${(Math.random() * 4 + 1).toFixed(2)} GB`,
        version: `1.${i}`,
        author: `Author ${i + 1}`,
        tags: ['sd1.5', 'checkpoint', query.toLowerCase()],
        downloads: Math.floor(Math.random() * 100000),
        rating: +(Math.random() * 2 + 3).toFixed(1),
      },
      verificationStatus: 'pending',
    };
  });
}

function generateReasoning(
  query: string,
  backend: SearchBackend,
  confidence: SearchConfidence,
  index: number
): string {
  const reasons = {
    HIGH: [
      `Exact name match found in ${backend} repository with verified hash`,
      `Strong semantic similarity (0.95) to query "${query}" with validated metadata`,
      `Official model from known author with high download count and positive ratings`,
    ],
    MEDIUM: [
      `Partial name match with similar model architecture`,
      `Found via ${backend} with good metadata match but unverified hash`,
      `Popular model with matching tags but slightly different version`,
    ],
    LOW: [
      `Weak semantic match, may require manual verification`,
      `Found via ${backend} but metadata incomplete or outdated`,
      `Alternative model with similar purpose but different architecture`,
    ],
    UNCERTAIN: [
      `Multiple conflicting matches found, manual selection required`,
      `Model name ambiguous across ${backend} sources`,
      `Insufficient metadata to determine correct model version`,
    ],
  };

  const reasonList = reasons[confidence];
  return reasonList[index % reasonList.length];
}

export class AgenticSearchService {
  private activeRuns: Map<string, SearchRun> = new Map();

  // Create a new search run
  async createSearchRun(query: string, strategy: SearchBackend[]): Promise<SearchRun> {
    const run: SearchRun = {
      id: generateId(),
      query,
      status: 'idle',
      currentPhase: 'initial',
      strategy,
      retryCount: 0,
      steps: [],
      candidates: [],
      logs: [],
    };

    this.activeRuns.set(run.id, run);
    this.addLog(run, 'info', `Search run created for query: "${query}"`);
    this.addLog(run, 'info', `Strategy: ${strategy.join(' → ')}`);

    return run;
  }

  // Execute search with the configured strategy
  async executeSearch(runId: string): Promise<SearchRun> {
    const run = this.activeRuns.get(runId);
    if (!run) throw new Error('Search run not found');

    run.status = 'running';
    run.startTime = new Date().toISOString();
    this.addLog(run, 'info', 'Starting search execution');

    try {
      // Phase 1: Initial search with first backend
      await this.executePhase(run, 'initial', run.strategy[0]);

      // If no HIGH confidence results, try fallback backends
      const highConfidenceCandidates = run.candidates.filter(c => c.confidence === 'HIGH');

      if (highConfidenceCandidates.length === 0 && run.strategy.length > 1) {
        this.addLog(run, 'warning', 'No high-confidence results, initiating fallback phase');
        run.currentPhase = 'fallback';

        for (let i = 1; i < run.strategy.length; i++) {
          await this.executePhase(run, 'fallback', run.strategy[i]);

          const newHighConfidence = run.candidates.filter(c => c.confidence === 'HIGH');
          if (newHighConfidence.length > 0) {
            this.addLog(run, 'info', `High confidence result found via ${run.strategy[i]}`);
            break;
          }
        }
      }

      // Check if we have uncertain results that need resolution
      const uncertainCandidates = run.candidates.filter(c => c.confidence === 'UNCERTAIN');
      if (uncertainCandidates.length > 0) {
        run.currentPhase = 'doubt_resolution';
        this.addLog(run, 'warning', `${uncertainCandidates.length} uncertain candidates require manual selection`);
      } else {
        run.currentPhase = 'complete';
      }

      run.status = 'completed';
      run.endTime = new Date().toISOString();
      run.duration = new Date(run.endTime).getTime() - new Date(run.startTime!).getTime();

      this.addLog(run, 'info', `Search completed in ${(run.duration / 1000).toFixed(2)}s`);
      this.addLog(run, 'info', `Found ${run.candidates.length} candidates total`);

    } catch (error: any) {
      run.status = 'failed';
      run.currentPhase = 'failed';
      this.addLog(run, 'error', `Search failed: ${error.message}`);
    }

    return run;
  }

  // Execute a single phase of the search
  private async executePhase(
    run: SearchRun,
    phase: SearchPhase,
    backend: SearchBackend
  ): Promise<void> {
    const step: SearchStep = {
      id: `step-${run.steps.length}`,
      phase,
      backend,
      status: 'running',
      timestamp: new Date().toISOString(),
      message: `Searching ${backend} for "${run.query}"`,
    };

    run.steps.push(step);
    run.currentBackend = backend;
    this.addLog(run, 'info', `Phase ${phase}: Querying ${backend}`);

    const startTime = Date.now();

    try {
      // Simulate API call
      await delay(1500 + Math.random() * 1000);

      // Generate mock results
      const candidateCount = Math.floor(Math.random() * 3) + 1;
      const newCandidates = generateMockCandidates(run.query, backend, candidateCount);

      run.candidates.push(...newCandidates);

      step.status = 'success';
      step.candidatesFound = candidateCount;
      step.duration = Date.now() - startTime;
      step.message = `Found ${candidateCount} candidates from ${backend}`;

      this.addLog(run, 'info', `${backend} returned ${candidateCount} candidates`);

      newCandidates.forEach((candidate, i) => {
        this.addLog(run, 'debug', `  [${i + 1}] ${candidate.modelName} - ${candidate.confidence} (${candidate.confidenceScore}%)`);
      });

    } catch (error: any) {
      step.status = 'failed';
      step.error = error.message;
      step.duration = Date.now() - startTime;
      this.addLog(run, 'error', `${backend} search failed: ${error.message}`);
    }
  }

  // Retry search with a different strategy
  async retrySearch(runId: string, newStrategy: SearchBackend[]): Promise<SearchRun> {
    const run = this.activeRuns.get(runId);
    if (!run) throw new Error('Search run not found');

    this.addLog(run, 'info', `Retrying search with new strategy: ${newStrategy.join(' → ')}`);

    // Reset the run
    run.strategy = newStrategy;
    run.retryCount++;
    run.steps = [];
    run.candidates = [];
    run.status = 'idle';
    run.currentPhase = 'initial';

    return this.executeSearch(runId);
  }

  // Select a candidate from uncertain results
  async selectCandidate(runId: string, candidateId: string): Promise<SearchRun> {
    const run = this.activeRuns.get(runId);
    if (!run) throw new Error('Search run not found');

    const candidate = run.candidates.find(c => c.id === candidateId);
    if (!candidate) throw new Error('Candidate not found');

    run.selectedCandidate = candidate;
    run.currentPhase = 'complete';

    this.addLog(run, 'info', `User selected: ${candidate.modelName} from ${candidate.source}`);

    return run;
  }

  // Get search run by ID
  getSearchRun(runId: string): SearchRun | undefined {
    return this.activeRuns.get(runId);
  }

  // Add log entry
  private addLog(run: SearchRun, level: SearchLogEntry['level'], message: string, details?: any): void {
    run.logs.push({
      id: generateLogId(),
      timestamp: new Date().toISOString(),
      level,
      message,
      details,
    });
  }

  // Get all active runs
  getAllRuns(): SearchRun[] {
    return Array.from(this.activeRuns.values());
  }
}

// Export singleton instance
export const agenticSearchService = new AgenticSearchService();
