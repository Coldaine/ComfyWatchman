import {
  SearchResult,
  SearchCandidate,
  SearchReasoningStep,
  SearchBackend,
  SearchPhase,
  SearchStatus,
  ModelType
} from '../types';

// Mock search service for Agentic Search Management
// In production, this would connect to the ComfyWatchman backend

const MOCK_SEARCH_DELAY = 1500;

const generateMockCandidates = (query: string, backend: SearchBackend): SearchCandidate[] => {
  const backends: SearchBackend[] = ['civitai', 'huggingface', 'modelscope'];
  const types: ModelType[] = ['Checkpoint', 'LORA', 'VAE', 'ControlNet'];

  return Array.from({ length: Math.floor(Math.random() * 3) + 1 }, (_, i) => ({
    id: `candidate-${backend}-${i}`,
    name: `${query}-${backend}-model-${i + 1}`,
    source: backend,
    url: `https://${backend}.com/models/${query.toLowerCase().replace(/\s+/g, '-')}-${i}`,
    confidence: Math.random() * 0.4 + 0.4, // 0.4 - 0.8
    matchScore: Math.random() * 0.5 + 0.5, // 0.5 - 1.0
    reasoning: `Found potential match on ${backend}. Model name similarity: ${(Math.random() * 0.3 + 0.7).toFixed(2)}. Type matches query context.`,
    metadata: {
      type: types[Math.floor(Math.random() * types.length)],
      size: `${(Math.random() * 5 + 1).toFixed(2)} GB`,
      downloads: Math.floor(Math.random() * 50000) + 1000,
      rating: Math.random() * 2 + 3, // 3-5 stars
      lastUpdated: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    },
  }));
};

const simulateSearchPhase = async (
  query: string,
  phase: SearchPhase,
  backends: SearchBackend[],
  existingSteps: SearchReasoningStep[]
): Promise<{
  steps: SearchReasoningStep[];
  candidates: SearchCandidate[];
  status: SearchStatus;
  confidence: number;
}> => {
  const newSteps: SearchReasoningStep[] = [];
  const allCandidates: SearchCandidate[] = [];

  if (phase === 'phase1') {
    // Phase 1: Civitai API Search
    const backend: SearchBackend = 'civitai';

    newSteps.push({
      id: `step-${Date.now()}-1`,
      timestamp: new Date().toISOString(),
      phase: 'phase1',
      backend,
      action: `Searching Civitai API for "${query}"`,
      reasoning: 'Starting with Civitai as primary model repository. High success rate for ComfyUI models.',
      result: 'success',
    });

    await new Promise(resolve => setTimeout(resolve, MOCK_SEARCH_DELAY));

    const candidates = generateMockCandidates(query, backend);
    allCandidates.push(...candidates);

    const maxConfidence = Math.max(...candidates.map(c => c.confidence));

    if (maxConfidence > 0.7) {
      newSteps.push({
        id: `step-${Date.now()}-2`,
        timestamp: new Date().toISOString(),
        phase: 'phase1',
        backend,
        action: 'High confidence match found',
        reasoning: `Found ${candidates.length} candidate(s) with max confidence ${maxConfidence.toFixed(2)}. Primary search successful.`,
        confidence: maxConfidence,
        result: 'success',
      });

      return {
        steps: newSteps,
        candidates: allCandidates,
        status: 'found',
        confidence: maxConfidence,
      };
    } else {
      newSteps.push({
        id: `step-${Date.now()}-2`,
        timestamp: new Date().toISOString(),
        phase: 'phase1',
        backend,
        action: 'Confidence below threshold',
        reasoning: `Max confidence ${maxConfidence.toFixed(2)} below 0.7 threshold. Proceeding to Phase 2 for additional sources.`,
        confidence: maxConfidence,
        result: 'uncertain',
      });
    }
  }

  if (phase === 'phase2') {
    // Phase 2: Web Search + HuggingFace
    const backends: SearchBackend[] = ['huggingface', 'web'];

    for (const backend of backends) {
      newSteps.push({
        id: `step-${Date.now()}-${backend}`,
        timestamp: new Date().toISOString(),
        phase: 'phase2',
        backend,
        action: `Expanding search to ${backend}`,
        reasoning: `Phase 1 insufficient. Searching ${backend} for additional candidates.`,
        result: 'success',
      });

      await new Promise(resolve => setTimeout(resolve, MOCK_SEARCH_DELAY));

      const candidates = generateMockCandidates(query, backend);
      allCandidates.push(...candidates);
    }

    const allConfidences = allCandidates.map(c => c.confidence);
    const maxConfidence = Math.max(...allConfidences);

    if (maxConfidence > 0.65) {
      newSteps.push({
        id: `step-${Date.now()}-phase2-complete`,
        timestamp: new Date().toISOString(),
        phase: 'phase2',
        backend: 'qwen',
        action: 'Phase 2 analysis complete',
        reasoning: `Combined ${allCandidates.length} candidates from multiple sources. Max confidence: ${maxConfidence.toFixed(2)}.`,
        confidence: maxConfidence,
        result: 'success',
      });

      return {
        steps: newSteps,
        candidates: allCandidates,
        status: 'found',
        confidence: maxConfidence,
      };
    } else {
      newSteps.push({
        id: `step-${Date.now()}-phase2-uncertain`,
        timestamp: new Date().toISOString(),
        phase: 'phase2',
        backend: 'qwen',
        action: 'Insufficient confidence across all sources',
        reasoning: `After searching ${allCandidates.length} sources, max confidence ${maxConfidence.toFixed(2)} still below certainty threshold. Entering doubt handling.`,
        confidence: maxConfidence,
        result: 'uncertain',
      });
    }
  }

  if (phase === 'phase3') {
    // Phase 3: Doubt Handling - require manual selection
    newSteps.push({
      id: `step-${Date.now()}-doubt`,
      timestamp: new Date().toISOString(),
      phase: 'phase3',
      backend: 'qwen',
      action: 'Manual review required',
      reasoning: `Multiple candidates found but none exceed confidence threshold. ${allCandidates.length} candidates available for manual selection.`,
      result: 'uncertain',
    });

    return {
      steps: newSteps,
      candidates: allCandidates,
      status: 'uncertain',
      confidence: allCandidates.length > 0 ? Math.max(...allCandidates.map(c => c.confidence)) : 0,
    };
  }

  return {
    steps: newSteps,
    candidates: allCandidates,
    status: 'failed',
    confidence: 0,
  };
};

export const performAgenticSearch = async (
  query: string,
  backendOrder: SearchBackend[] = ['qwen', 'civitai', 'huggingface']
): Promise<SearchResult> => {
  const startTime = new Date().toISOString();
  const searchId = `search-${Date.now()}`;

  let allSteps: SearchReasoningStep[] = [];
  let allCandidates: SearchCandidate[] = [];
  let currentStatus: SearchStatus = 'searching';
  let confidence = 0;

  // Initial step
  allSteps.push({
    id: `step-${Date.now()}-init`,
    timestamp: startTime,
    phase: 'phase1',
    backend: 'qwen',
    action: 'Initializing agentic search',
    reasoning: `Query: "${query}". Backend order: ${backendOrder.join(' → ')}. Starting multi-phase search protocol.`,
    result: 'success',
  });

  // Phase 1
  const phase1Result = await simulateSearchPhase(query, 'phase1', backendOrder, allSteps);
  allSteps.push(...phase1Result.steps);
  allCandidates.push(...phase1Result.candidates);

  if (phase1Result.status === 'found') {
    return {
      id: searchId,
      query,
      status: 'found',
      currentPhase: 'completed',
      confidence: phase1Result.confidence,
      candidates: allCandidates,
      selectedCandidate: allCandidates[0],
      reasoningSteps: allSteps,
      startTime,
      endTime: new Date().toISOString(),
      duration: Date.now() - new Date(startTime).getTime(),
      backendOrder,
      retryCount: 0,
      maxRetries: 3,
    };
  }

  // Phase 2
  const phase2Result = await simulateSearchPhase(query, 'phase2', backendOrder, allSteps);
  allSteps.push(...phase2Result.steps);
  allCandidates.push(...phase2Result.candidates);

  if (phase2Result.status === 'found') {
    return {
      id: searchId,
      query,
      status: 'found',
      currentPhase: 'completed',
      confidence: phase2Result.confidence,
      candidates: allCandidates,
      selectedCandidate: allCandidates[0],
      reasoningSteps: allSteps,
      startTime,
      endTime: new Date().toISOString(),
      duration: Date.now() - new Date(startTime).getTime(),
      backendOrder,
      retryCount: 0,
      maxRetries: 3,
    };
  }

  // Phase 3 - Manual intervention needed
  const phase3Result = await simulateSearchPhase(query, 'phase3', backendOrder, allSteps);
  allSteps.push(...phase3Result.steps);

  return {
    id: searchId,
    query,
    status: 'uncertain',
    currentPhase: 'phase3',
    confidence: phase3Result.confidence,
    candidates: allCandidates,
    reasoningSteps: allSteps,
    startTime,
    endTime: new Date().toISOString(),
    duration: Date.now() - new Date(startTime).getTime(),
    backendOrder,
    retryCount: 0,
    maxRetries: 3,
  };
};

export const retrySearchWithBackend = async (
  originalSearch: SearchResult,
  newBackend: SearchBackend
): Promise<SearchResult> => {
  const newBackendOrder = [newBackend, ...originalSearch.backendOrder.filter(b => b !== newBackend)];

  const result = await performAgenticSearch(originalSearch.query, newBackendOrder);

  return {
    ...result,
    retryCount: originalSearch.retryCount + 1,
  };
};

export const selectCandidate = (
  searchResult: SearchResult,
  candidateId: string
): SearchResult => {
  const selected = searchResult.candidates.find(c => c.id === candidateId);

  if (!selected) {
    throw new Error(`Candidate ${candidateId} not found`);
  }

  return {
    ...searchResult,
    status: 'found',
    currentPhase: 'completed',
    selectedCandidate: selected,
    confidence: selected.confidence,
    endTime: new Date().toISOString(),
    reasoningSteps: [
      ...searchResult.reasoningSteps,
      {
        id: `step-${Date.now()}-manual`,
        timestamp: new Date().toISOString(),
        phase: 'completed',
        backend: selected.source,
        action: 'Manual candidate selection',
        reasoning: `User selected candidate "${selected.name}" from ${selected.source} with confidence ${selected.confidence.toFixed(2)}.`,
        confidence: selected.confidence,
        result: 'success',
      },
    ],
  };
};
