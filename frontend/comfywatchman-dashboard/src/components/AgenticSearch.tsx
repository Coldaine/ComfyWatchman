import { useState, useEffect } from 'react';
import { SearchRun, SearchBackend, SearchStrategy, SearchCandidate } from '../types';
import { agenticSearchService } from '../services/agentic-search-service';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import {
  Search,
  Play,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
  Settings,
  ChevronRight,
  Database,
  Globe,
  Cloud,
  Activity,
  FileText
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { toast } from 'sonner';

const PREDEFINED_STRATEGIES: SearchStrategy[] = [
  {
    name: 'API First',
    backends: ['API', 'Web', 'HuggingFace'],
    description: 'Start with API, fallback to web scraping and HuggingFace',
  },
  {
    name: 'HuggingFace Priority',
    backends: ['HuggingFace', 'API', 'Web'],
    description: 'Prioritize HuggingFace models, fallback to API and web',
  },
  {
    name: 'Web Scraping Only',
    backends: ['Web'],
    description: 'Only use web scraping for model discovery',
  },
  {
    name: 'Multi-Source Parallel',
    backends: ['API', 'HuggingFace', 'Web'],
    description: 'Query all sources in order for maximum coverage',
  },
];

const BACKEND_ICONS: Record<SearchBackend, any> = {
  API: Database,
  Web: Globe,
  HuggingFace: Cloud,
};

const BACKEND_COLORS: Record<SearchBackend, string> = {
  API: 'text-blue-500',
  Web: 'text-green-500',
  HuggingFace: 'text-purple-500',
};

function ConfidenceMeter({ confidence, score }: { confidence: SearchCandidate['confidence']; score: number }) {
  const colors = {
    HIGH: 'bg-green-500',
    MEDIUM: 'bg-yellow-500',
    LOW: 'bg-orange-500',
    UNCERTAIN: 'bg-red-500',
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Confidence</span>
        <Badge variant={confidence === 'HIGH' ? 'default' : confidence === 'UNCERTAIN' ? 'destructive' : 'secondary'}>
          {confidence}
        </Badge>
      </div>
      <div className="relative h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`absolute left-0 top-0 h-full transition-all ${colors[confidence]}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <div className="text-right text-xs text-muted-foreground">{score}%</div>
    </div>
  );
}

function PhaseTimeline({ run }: { run: SearchRun }) {
  const getPhaseStatus = (phaseId: string) => {
    const phaseSteps = run.steps.filter(s => s.phase === phaseId);

    if (phaseSteps.length === 0) {
      if (run.currentPhase === phaseId && run.status === 'running') return 'running';
      return 'pending';
    }

    if (phaseSteps.some(s => s.status === 'running')) return 'running';
    if (phaseSteps.some(s => s.status === 'success')) return 'success';
    if (phaseSteps.some(s => s.status === 'failed')) return 'failed';
    return 'pending';
  };

  const phases = [
    { id: 'initial', label: 'Initial Search', icon: Search },
    { id: 'fallback', label: 'Fallback Search', icon: RotateCcw },
    { id: 'doubt_resolution', label: 'Doubt Resolution', icon: AlertCircle },
  ];

  return (
    <div className="flex items-center gap-2">
      {phases.map((phase, index) => {
        const status = getPhaseStatus(phase.id);
        const Icon = phase.icon;
        const isActive = run.currentPhase === phase.id && run.status === 'running';
        const isPast = status === 'success' || (
          ['initial', 'fallback', 'doubt_resolution'].indexOf(run.currentPhase) >
          ['initial', 'fallback', 'doubt_resolution'].indexOf(phase.id)
        ) || (run.status === 'completed');

        return (
          <div key={phase.id} className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
              isActive ? 'border-primary bg-primary/10' :
              isPast ? 'border-green-500/30 bg-green-500/10' :
              'border-border bg-card'
            }`}>
              <Icon className={`w-4 h-4 ${
                isActive ? 'text-primary' :
                isPast ? 'text-green-500' :
                'text-muted-foreground'
              }`} />
              <span className={`text-sm ${isActive || isPast ? '' : 'text-muted-foreground'}`}>
                {phase.label}
              </span>
              {status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
              {status === 'success' && <CheckCircle2 className="w-3 h-3 text-green-500" />}
              {status === 'failed' && <XCircle className="w-3 h-3 text-red-500" />}
            </div>
            {index < phases.length - 1 && (
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function CandidateCard({
  candidate,
  onSelect,
  isSelected
}: {
  candidate: SearchCandidate;
  onSelect: () => void;
  isSelected: boolean;
}) {
  const Icon = BACKEND_ICONS[candidate.source];
  const colorClass = BACKEND_COLORS[candidate.source];

  return (
    <Card
      className={`p-4 cursor-pointer transition-all hover:border-primary ${
        isSelected ? 'border-primary bg-primary/5' : ''
      }`}
      onClick={onSelect}
    >
      <div className="space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Icon className={`w-4 h-4 ${colorClass}`} />
              <span className="text-sm text-muted-foreground">{candidate.source}</span>
            </div>
            <h4 className="truncate">{candidate.modelName}</h4>
          </div>
          {isSelected && <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />}
        </div>

        <ConfidenceMeter confidence={candidate.confidence} score={candidate.confidenceScore} />

        <div className="text-sm text-muted-foreground bg-muted/50 rounded p-2">
          {candidate.reasoning}
        </div>

        {candidate.metadata && (
          <div className="flex flex-wrap gap-2 text-xs">
            {candidate.metadata.size && (
              <Badge variant="outline">{candidate.metadata.size}</Badge>
            )}
            {candidate.metadata.version && (
              <Badge variant="outline">v{candidate.metadata.version}</Badge>
            )}
            {candidate.metadata.downloads && (
              <Badge variant="outline">{candidate.metadata.downloads.toLocaleString()} downloads</Badge>
            )}
            {candidate.metadata.rating && (
              <Badge variant="outline">★ {candidate.metadata.rating}</Badge>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

function LogsPanel({ run }: { run: SearchRun }) {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'text-red-500';
      case 'warning': return 'text-yellow-500';
      case 'info': return 'text-blue-500';
      case 'debug': return 'text-muted-foreground';
      default: return '';
    }
  };

  return (
    <ScrollArea className="h-[400px]">
      <div className="space-y-1 font-mono text-xs">
        {run.logs.map((log) => (
          <div key={log.id} className="flex gap-2 p-1 hover:bg-muted/50 rounded">
            <span className="text-muted-foreground shrink-0">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className={`shrink-0 uppercase ${getLevelColor(log.level)}`}>
              [{log.level}]
            </span>
            <span className="flex-1">{log.message}</span>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}

export function AgenticSearch() {
  const [query, setQuery] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState<SearchStrategy>(PREDEFINED_STRATEGIES[0]);
  const [currentRun, setCurrentRun] = useState<SearchRun | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  const handleStartSearch = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setIsSearching(true);
    try {
      const run = await agenticSearchService.createSearchRun(query, selectedStrategy.backends);
      setCurrentRun(run);

      const updatedRun = await agenticSearchService.executeSearch(run.id);
      setCurrentRun(updatedRun);

      toast.success('Search completed');
    } catch (error: any) {
      toast.error(`Search failed: ${error.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  const handleRetry = async (newStrategy: SearchStrategy) => {
    if (!currentRun) return;

    setIsSearching(true);
    setSelectedStrategy(newStrategy);
    try {
      const updatedRun = await agenticSearchService.retrySearch(currentRun.id, newStrategy.backends);
      setCurrentRun(updatedRun);
      toast.success('Search retried with new strategy');
    } catch (error: any) {
      toast.error(`Retry failed: ${error.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectCandidate = async (candidateId: string) => {
    if (!currentRun) return;

    const previousId = selectedCandidateId;
    setSelectedCandidateId(candidateId);

    try {
      const updatedRun = await agenticSearchService.selectCandidate(currentRun.id, candidateId);
      setCurrentRun(updatedRun);
      toast.success('Candidate selected');
    } catch (error: any) {
      toast.error(`Selection failed: ${error.message}`);
      setSelectedCandidateId(previousId);
    }
  };

  const groupedCandidates = currentRun?.candidates.reduce((acc, candidate) => {
    if (!acc[candidate.confidence]) {
      acc[candidate.confidence] = [];
    }
    acc[candidate.confidence].push(candidate);
    return acc;
  }, {} as Record<string, SearchCandidate[]>) || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2>Agentic Search Management</h2>
        <p className="text-muted-foreground mt-1">
          Multi-phase AI model discovery with confidence scoring and intelligent fallback
        </p>
      </div>

      {/* Search Configuration */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm mb-2 block">Search Query</label>
              <Input
                placeholder="Enter model name or description..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleStartSearch()}
              />
            </div>
            <div className="w-64">
              <label className="text-sm mb-2 block">Search Strategy</label>
              <Select
                value={selectedStrategy.name}
                onValueChange={(value) => {
                  const strategy = PREDEFINED_STRATEGIES.find(s => s.name === value);
                  if (strategy) setSelectedStrategy(strategy);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PREDEFINED_STRATEGIES.map((strategy) => (
                    <SelectItem key={strategy.name} value={strategy.name}>
                      {strategy.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="text-sm text-muted-foreground">{selectedStrategy.description}</div>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-muted-foreground">Backend Order:</span>
                {selectedStrategy.backends.map((backend, index) => {
                  const Icon = BACKEND_ICONS[backend];
                  const colorClass = BACKEND_COLORS[backend];
                  return (
                    <div key={backend} className="flex items-center gap-1">
                      <Badge variant="outline" className="gap-1">
                        <Icon className={`w-3 h-3 ${colorClass}`} />
                        {backend}
                      </Badge>
                      {index < selectedStrategy.backends.length - 1 && (
                        <ChevronRight className="w-3 h-3 text-muted-foreground" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
            <Button
              onClick={handleStartSearch}
              disabled={isSearching || !query.trim()}
              size="lg"
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start Search
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* Search Run Console */}
      {currentRun && (
        <div className="space-y-6">
          {/* Status Bar */}
          <Card className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Status</div>
                  <div className="flex items-center gap-2 mt-1">
                    {currentRun.status === 'running' && (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                    )}
                    {currentRun.status === 'completed' && (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    )}
                    {currentRun.status === 'failed' && (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="capitalize">{currentRun.status}</span>
                  </div>
                </div>
                <Separator orientation="vertical" className="h-10" />
                <div>
                  <div className="text-sm text-muted-foreground">Query</div>
                  <div className="mt-1">{currentRun.query}</div>
                </div>
                <Separator orientation="vertical" className="h-10" />
                <div>
                  <div className="text-sm text-muted-foreground">Candidates Found</div>
                  <div className="mt-1">{currentRun.candidates.length}</div>
                </div>
                {currentRun.duration && (
                  <>
                    <Separator orientation="vertical" className="h-10" />
                    <div>
                      <div className="text-sm text-muted-foreground">Duration</div>
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="w-4 h-4" />
                        {(currentRun.duration / 1000).toFixed(2)}s
                      </div>
                    </div>
                  </>
                )}
              </div>
              <div className="flex gap-2">
                {currentRun.status === 'completed' && (
                  <Select onValueChange={(value) => {
                    const strategy = PREDEFINED_STRATEGIES.find(s => s.name === value);
                    if (strategy) handleRetry(strategy);
                  }}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Retry with strategy..." />
                    </SelectTrigger>
                    <SelectContent>
                      {PREDEFINED_STRATEGIES.map((strategy) => (
                        <SelectItem key={strategy.name} value={strategy.name}>
                          {strategy.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            </div>

            <PhaseTimeline run={currentRun} />
          </Card>

          {/* Results and Logs */}
          <div className="grid grid-cols-2 gap-6">
            {/* Candidates */}
            <Card className="p-6">
              <Tabs defaultValue="all">
                <div className="flex items-center justify-between mb-4">
                  <h3>Search Results</h3>
                  <TabsList>
                    <TabsTrigger value="all">
                      All ({currentRun.candidates.length})
                    </TabsTrigger>
                    <TabsTrigger value="high">
                      High ({groupedCandidates.HIGH?.length || 0})
                    </TabsTrigger>
                    <TabsTrigger value="uncertain">
                      Uncertain ({groupedCandidates.UNCERTAIN?.length || 0})
                    </TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="all" className="space-y-3">
                  <ScrollArea className="h-[500px] pr-4">
                    <div className="space-y-3">
                      {currentRun.candidates.map((candidate) => (
                        <CandidateCard
                          key={candidate.id}
                          candidate={candidate}
                          onSelect={() => handleSelectCandidate(candidate.id)}
                          isSelected={selectedCandidateId === candidate.id || currentRun.selectedCandidate?.id === candidate.id}
                        />
                      ))}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="high" className="space-y-3">
                  <ScrollArea className="h-[500px] pr-4">
                    <div className="space-y-3">
                      {groupedCandidates.HIGH?.map((candidate) => (
                        <CandidateCard
                          key={candidate.id}
                          candidate={candidate}
                          onSelect={() => handleSelectCandidate(candidate.id)}
                          isSelected={selectedCandidateId === candidate.id || currentRun.selectedCandidate?.id === candidate.id}
                        />
                      )) || <div className="text-center text-muted-foreground py-8">No high confidence results</div>}
                    </div>
                  </ScrollArea>
                </TabsContent>

                <TabsContent value="uncertain" className="space-y-3">
                  <ScrollArea className="h-[500px] pr-4">
                    <div className="space-y-3">
                      {groupedCandidates.UNCERTAIN?.length > 0 ? (
                        <>
                          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-sm">
                            <div className="flex items-start gap-2">
                              <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5" />
                              <div>
                                <div className="text-yellow-500 mb-1">Manual Selection Required</div>
                                <div className="text-muted-foreground">
                                  These candidates have uncertain confidence scores. Please review and select the correct model manually.
                                </div>
                              </div>
                            </div>
                          </div>
                          {groupedCandidates.UNCERTAIN.map((candidate) => (
                            <CandidateCard
                              key={candidate.id}
                              candidate={candidate}
                              onSelect={() => handleSelectCandidate(candidate.id)}
                              isSelected={selectedCandidateId === candidate.id || currentRun.selectedCandidate?.id === candidate.id}
                            />
                          ))}
                        </>
                      ) : (
                        <div className="text-center text-muted-foreground py-8">No uncertain results</div>
                      )}
                    </div>
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </Card>

            {/* Logs */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3>Execution Logs</h3>
                <Badge variant="outline">
                  <FileText className="w-3 h-3 mr-1" />
                  {currentRun.logs.length} entries
                </Badge>
              </div>
              <LogsPanel run={currentRun} />
            </Card>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!currentRun && (
        <Card className="p-12">
          <div className="text-center max-w-md mx-auto">
            <Activity className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="mb-2">No Active Search</h3>
            <p className="text-muted-foreground text-sm">
              Enter a search query and select a strategy to begin multi-phase model discovery
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
