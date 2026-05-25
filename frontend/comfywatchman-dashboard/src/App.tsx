import { useState, useMemo, useEffect, useRef } from 'react';
import { Model, ModelType } from './types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Input } from './components/ui/input';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { StatCard } from './components/StatCard';
import { ModelCard } from './components/ModelCard';
import { WorkflowCard } from './components/WorkflowCard';
import { DependencyGraph } from './components/DependencyGraph';
import { ActivityLog } from './components/ActivityLog';
import { StorageManagement } from './components/StorageManagement';
import { QuickActions } from './components/QuickActions';
import { AdvancedFeatures } from './components/AdvancedFeatures';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoadingScreen } from './components/LoadingScreen';
import { KeyboardShortcutsDialog } from './components/KeyboardShortcutsDialog';
import { ExportImportDialog } from './components/ExportImportDialog';
import { SettingsDialog } from './components/SettingsDialog';
import { AgenticSearch } from './components/AgenticSearch';
import { VariantGallery } from './components/VariantGallery';
import { Toaster } from './components/ui/sonner';
import { useComfyUI } from './hooks/useComfyUI';
import { useDebounce } from './hooks/useDebounce';
import { useUserPreferences, UserPreferencesProvider } from './hooks/useUserPreferences';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcut';
import {
  Search,
  Filter,
  FileBox,
  Wand2,
  Layers,
  Network,
  HardDrive,
  MoreHorizontal,
  SortAsc,
  Download,
  BarChart3,
  Home,
  Zap,
  Bot,
  Palette
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './components/ui/dropdown-menu';

function AppContent() {
  const { preferences } = useUserPreferences();
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'advanced' | 'watchman' | 'variants'>('dashboard');
  const [activeTab, setActiveTab] = useState(preferences.defaultTab);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedModelType, setSelectedModelType] = useState<ModelType | 'all'>(preferences.defaultModelType);
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'date' | 'usage'>(preferences.defaultSortBy);

  // Debounce search query to avoid excessive re-renders
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  // Ref for search input
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Fetch data with loading and error states
  const { models, workflows, activityLog, loading, error, refetch } = useComfyUI({
    query: debouncedSearchQuery,
    type: selectedModelType === 'all' ? undefined : selectedModelType,
  });

  // Auto-refresh if enabled
  useEffect(() => {
    if (!preferences.autoRefresh) return;

    const interval = setInterval(() => {
      refetch();
    }, preferences.autoRefreshInterval * 1000);

    return () => clearInterval(interval);
  }, [preferences.autoRefresh, preferences.autoRefreshInterval, refetch]);

  // Calculate stats (before any conditional returns)
  const totalModels = models.length;
  const missingModels = models.filter(m => m.status === 'missing').length;
  const totalWorkflows = workflows.length;
  const readyWorkflows = workflows.filter(w => w.status === 'ready').length;

  // Sort models (filtering already done by useComfyUI hook)
  const sortedModels = useMemo(() => {
    const sorted = [...models];
    switch (sortBy) {
      case 'name':
        sorted.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'size':
        sorted.sort((a, b) => b.sizeBytes - a.sizeBytes);
        break;
      case 'date':
        sorted.sort((a, b) => new Date(b.dateAdded).getTime() - new Date(a.dateAdded).getTime());
        break;
      case 'usage':
        sorted.sort((a, b) => (b.usageCount || 0) - (a.usageCount || 0));
        break;
    }
    return sorted;
  }, [models, sortBy]);

  // Count models by type from actual data
  const modelTypeCounts = useMemo(() => {
    const counts: Record<string, number> = { all: models.length };
    models.forEach(m => {
      counts[m.type] = (counts[m.type] || 0) + 1;
    });
    return counts;
  }, [models]);

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      shortcut: { key: 'k', ctrl: true },
      callback: () => searchInputRef.current?.focus()
    },
    {
      shortcut: { key: 'm', ctrl: true },
      callback: () => setActiveTab('models')
    },
    {
      shortcut: { key: 'w', ctrl: true },
      callback: () => setActiveTab('workflows')
    },
    {
      shortcut: { key: 'd', ctrl: true },
      callback: () => setActiveTab('dependencies')
    },
    {
      shortcut: { key: 'a', ctrl: true, shift: true },
      callback: () => setCurrentPage(prev => prev === 'dashboard' ? 'advanced' : 'dashboard')
    },
    {
      shortcut: { key: 's', ctrl: true, shift: true },
      callback: () => setCurrentPage('watchman')
    },
  ], preferences.enableKeyboardShortcuts);

  // Show loading screen on initial load (after all hooks)
  if (loading && models.length === 0) {
    return <LoadingScreen message="Loading ComfyUI data..." />;
  }

  // Show error state (after all hooks)
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md">
          <h2 className="mb-2 text-destructive">Error Loading Data</h2>
          <p className="text-muted-foreground mb-4">{error.message}</p>
          <Button onClick={() => refetch()}>Try Again</Button>
        </div>
      </div>
    );
  }

  const modelTypes: Array<{ type: ModelType | 'all'; label: string; icon: any }> = [
    { type: 'all', label: 'All Models', icon: Filter },
    { type: 'Checkpoint', label: 'Checkpoints', icon: FileBox },
    { type: 'LORA', label: 'LORAs', icon: Wand2 },
    { type: 'VAE', label: 'VAE Models', icon: Layers },
    { type: 'CLIP', label: 'CLIP Models', icon: Network },
    { type: 'UNET', label: 'UNET Models', icon: Network },
    { type: 'ControlNet', label: 'ControlNet', icon: Network },
    { type: 'Upscale', label: 'Upscale', icon: HardDrive },
    { type: 'Other', label: 'Others', icon: MoreHorizontal },
  ];

  return (
    <div className="min-h-screen bg-background dark">
      <Toaster />

      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1>ComfyUI Manager</h1>
              <p className="text-muted-foreground mt-1">
                {currentPage === 'watchman'
                  ? 'ComfyWatchman - Intelligent Backend Services'
                  : currentPage === 'variants'
                  ? 'Donor UI variants'
                  : currentPage === 'advanced'
                  ? 'Advanced Features & Tools'
                  : 'Model & Workflow Management Dashboard'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={currentPage === 'dashboard' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentPage('dashboard')}
              >
                <Home className="w-4 h-4 mr-2" />
                Dashboard
              </Button>
              <Button
                variant={currentPage === 'advanced' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentPage('advanced')}
              >
                <Zap className="w-4 h-4 mr-2" />
                Advanced Features
              </Button>
              <Button
                variant={currentPage === 'watchman' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentPage('watchman')}
              >
                <Bot className="w-4 h-4 mr-2" />
                ComfyWatchman
              </Button>
              <Button
                variant={currentPage === 'variants' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCurrentPage('variants')}
              >
                <Palette className="w-4 h-4 mr-2" />
                UI Variants
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Download Queue ({missingModels})
              </Button>
              <ExportImportDialog />
              <SettingsDialog />
              <KeyboardShortcutsDialog />
            </div>
          </div>

          {/* Search Bar - Only show on dashboard */}
          {currentPage === 'dashboard' && (
            <div className="flex items-center gap-2 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                ref={searchInputRef}
                placeholder="Search models and workflows... (Ctrl+K)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <SortAsc className="w-4 h-4 mr-2" />
                  Sort: {sortBy}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setSortBy('name')}>
                  Name
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortBy('size')}>
                  Size
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortBy('date')}>
                  Date Added
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortBy('usage')}>
                  Most Used
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          )}
        </div>
      </header>

      <div className="container mx-auto px-6 py-6">
        {currentPage === 'watchman' ? (
          <AgenticSearch />
        ) : currentPage === 'variants' ? (
          <VariantGallery models={models} workflows={workflows} activityLog={activityLog} />
        ) : currentPage === 'advanced' ? (
          <AdvancedFeatures models={models} workflows={workflows} />
        ) : (
          <div className="grid grid-cols-12 gap-6">
            {/* Sidebar */}
            <aside className="col-span-3 space-y-6">
            <div className="space-y-3">
              <StatCard
                label="Total Models"
                value={totalModels}
                variant="default"
              />
              <StatCard
                label="Missing Models"
                value={missingModels}
                variant="danger"
              />
              <StatCard
                label="Total Workflows"
                value={totalWorkflows}
                variant="default"
              />
              <StatCard
                label="Ready Workflows"
                value={readyWorkflows}
                variant="success"
              />
            </div>

            <QuickActions />
            <StorageManagement models={models} />
            <ActivityLog activities={activityLog} />
          </aside>

          {/* Main Content */}
          <main className="col-span-9">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-6">
                <TabsTrigger value="models">
                  Models ({sortedModels.length})
                </TabsTrigger>
                <TabsTrigger value="workflows">
                  Workflows ({workflows.length})
                </TabsTrigger>
                <TabsTrigger value="dependencies">
                  Dependencies
                </TabsTrigger>
              </TabsList>

              <TabsContent value="models" className="space-y-6">
                {/* Model Type Filters */}
                <div className="flex flex-wrap gap-2">
                  {modelTypes.map(({ type, label, icon: Icon }) => {
                    const count = modelTypeCounts[type] || 0;

                    return (
                      <Button
                        key={type}
                        variant={selectedModelType === type ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedModelType(type)}
                        className="gap-2"
                      >
                        <Icon className="w-4 h-4" />
                        {label}
                        <Badge variant="secondary" className="ml-1">
                          {count}
                        </Badge>
                      </Button>
                    );
                  })}
                </div>

                {/* Missing Models Section */}
                {preferences.showMissingModelsAlert && selectedModelType === 'all' && missingModels > 0 && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-red-500">Missing Models ({missingModels})</h3>
                      <Button size="sm" variant="destructive">
                        <Download className="w-4 h-4 mr-2" />
                        Download All
                      </Button>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Some workflows cannot run due to missing model files
                    </p>
                  </div>
                )}

                {/* Models Grid */}
                <div className="grid grid-cols-2 gap-4">
                  {sortedModels.map((model) => (
                    <ModelCard
                      key={model.id}
                      model={model}
                      workflows={workflows}
                    />
                  ))}
                </div>

                {sortedModels.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    No models found matching your search
                  </div>
                )}
              </TabsContent>

              <TabsContent value="workflows" className="space-y-6">
                {/* Workflow Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <div className="text-green-500">Ready to Run</div>
                    <div className="text-2xl mt-1">{readyWorkflows}</div>
                  </div>
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <div className="text-red-500">Missing Models</div>
                    <div className="text-2xl mt-1">{totalWorkflows - readyWorkflows}</div>
                  </div>
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                    <div className="text-blue-500">Total Workflows</div>
                    <div className="text-2xl mt-1">{totalWorkflows}</div>
                  </div>
                </div>

                {/* Workflows List */}
                <div className="space-y-4">
                  {workflows.map((workflow) => (
                    <WorkflowCard key={workflow.id} workflow={workflow} />
                  ))}
                </div>

                {workflows.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    No workflows found matching your search
                  </div>
                )}
              </TabsContent>

              <TabsContent value="dependencies" className="space-y-6">
                <DependencyGraph models={models} workflows={workflows} />

                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="mb-4">Most Used Models</h3>
                    <div className="space-y-3">
                      {models
                        .filter(m => m.usageCount !== undefined)
                        .sort((a, b) => (b.usageCount || 0) - (a.usageCount || 0))
                        .slice(0, 5)
                        .map((model) => (
                          <div key={model.id} className="flex items-center justify-between">
                            <span className="text-sm truncate flex-1">{model.name}</span>
                            <Badge variant="outline">{model.usageCount} uses</Badge>
                          </div>
                        ))}
                    </div>
                  </div>

                  <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="mb-4">Popular Workflows</h3>
                    <div className="space-y-3">
                      {workflows
                        .filter(w => w.usageCount !== undefined)
                        .sort((a, b) => (b.usageCount || 0) - (a.usageCount || 0))
                        .slice(0, 5)
                        .map((workflow) => (
                          <div key={workflow.id} className="flex items-center justify-between">
                            <span className="text-sm truncate flex-1">{workflow.name}</span>
                            <Badge variant="outline">{workflow.usageCount} runs</Badge>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </main>
          </div>
        )}
      </div>
    </div>
  );
}

// Wrap the app with ErrorBoundary and UserPreferencesProvider
export default function App() {
  return (
    <ErrorBoundary>
      <UserPreferencesProvider>
        <AppContent />
      </UserPreferencesProvider>
    </ErrorBoundary>
  );
}
