import { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import {
  Save,
  Trash2,
  Download,
  Upload,
  Star,
  Copy,
  Edit
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Label } from './ui/label';
import { toast } from 'sonner';

interface Preset {
  id: string;
  name: string;
  description: string;
  workflow: string;
  parameters: {
    steps: number;
    cfg: number;
    sampler: string;
    scheduler: string;
    denoise: number;
    seed: number;
  };
  favorite: boolean;
  createdDate: string;
  usageCount: number;
}

const defaultPresets: Preset[] = [
  {
    id: '1',
    name: 'High Quality Portrait',
    description: 'Optimized for realistic portrait generation with fine details',
    workflow: 'Portrait Workflow',
    parameters: {
      steps: 30,
      cfg: 7.5,
      sampler: 'DPM++ 2M Karras',
      scheduler: 'Karras',
      denoise: 1.0,
      seed: -1
    },
    favorite: true,
    createdDate: '2024-01-15',
    usageCount: 47
  },
  {
    id: '2',
    name: 'Fast Draft',
    description: 'Quick generation with acceptable quality for testing',
    workflow: 'General Workflow',
    parameters: {
      steps: 15,
      cfg: 6.0,
      sampler: 'Euler a',
      scheduler: 'Normal',
      denoise: 0.8,
      seed: -1
    },
    favorite: false,
    createdDate: '2024-01-18',
    usageCount: 23
  },
  {
    id: '3',
    name: 'Landscape Excellence',
    description: 'Perfect for outdoor scenes and nature photography style',
    workflow: 'Landscape Workflow',
    parameters: {
      steps: 40,
      cfg: 8.0,
      sampler: 'DPM++ SDE Karras',
      scheduler: 'Karras',
      denoise: 1.0,
      seed: 42
    },
    favorite: true,
    createdDate: '2024-01-20',
    usageCount: 35
  },
  {
    id: '4',
    name: 'Artistic Style',
    description: 'Enhanced for creative and artistic outputs',
    workflow: 'Style Transfer',
    parameters: {
      steps: 35,
      cfg: 9.0,
      sampler: 'DPM++ 2M',
      scheduler: 'Exponential',
      denoise: 0.9,
      seed: -1
    },
    favorite: false,
    createdDate: '2024-01-22',
    usageCount: 18
  }
];

export function ParameterPresets() {
  const [presets, setPresets] = useState<Preset[]>(defaultPresets);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newPreset, setNewPreset] = useState({
    name: '',
    description: '',
    workflow: 'General Workflow'
  });

  const handleToggleFavorite = (id: string) => {
    setPresets(prev => prev.map(preset =>
      preset.id === id ? { ...preset, favorite: !preset.favorite } : preset
    ));
    toast.success('Favorite updated');
  };

  const handleDelete = (id: string) => {
    setPresets(prev => prev.filter(preset => preset.id !== id));
    toast.success('Preset deleted');
  };

  const handleDuplicate = (preset: Preset) => {
    const newPreset = {
      ...preset,
      id: Date.now().toString(),
      name: `${preset.name} (Copy)`,
      createdDate: new Date().toISOString().split('T')[0],
      usageCount: 0
    };
    setPresets(prev => [...prev, newPreset]);
    toast.success('Preset duplicated');
  };

  const handleCreatePreset = () => {
    const preset: Preset = {
      id: Date.now().toString(),
      name: newPreset.name,
      description: newPreset.description,
      workflow: newPreset.workflow,
      parameters: {
        steps: 30,
        cfg: 7.5,
        sampler: 'DPM++ 2M Karras',
        scheduler: 'Karras',
        denoise: 1.0,
        seed: -1
      },
      favorite: false,
      createdDate: new Date().toISOString().split('T')[0],
      usageCount: 0
    };

    setPresets(prev => [...prev, preset]);
    setIsCreateDialogOpen(false);
    setNewPreset({ name: '', description: '', workflow: 'General Workflow' });
    toast.success('Preset created successfully');
  };

  const handleExport = (preset: Preset) => {
    const json = JSON.stringify(preset, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${preset.name.replace(/\s+/g, '_')}.json`;
    a.click();
    toast.success('Preset exported');
  };

  const handleImport = () => {
    toast.success('Import dialog would open here');
  };

  const favorites = presets.filter(p => p.favorite);
  const regular = presets.filter(p => !p.favorite);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3>Parameter Presets</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Save and manage workflow parameter configurations
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleImport}>
              <Upload className="w-4 h-4 mr-2" />
              Import
            </Button>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Save className="w-4 h-4 mr-2" />
                  Create Preset
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Preset</DialogTitle>
                  <DialogDescription>
                    Save your current workflow parameters as a reusable preset
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="preset-name">Preset Name</Label>
                    <Input
                      id="preset-name"
                      placeholder="e.g., High Quality Portrait"
                      value={newPreset.name}
                      onChange={(e) => setNewPreset({ ...newPreset, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="preset-description">Description</Label>
                    <Textarea
                      id="preset-description"
                      placeholder="Describe what this preset is optimized for..."
                      value={newPreset.description}
                      onChange={(e) => setNewPreset({ ...newPreset, description: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="preset-workflow">Workflow</Label>
                    <Input
                      id="preset-workflow"
                      placeholder="Workflow name"
                      value={newPreset.workflow}
                      onChange={(e) => setNewPreset({ ...newPreset, workflow: e.target.value })}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreatePreset} disabled={!newPreset.name}>
                    Create Preset
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </Card>

      {/* Favorites Section */}
      {favorites.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
            <h4>Favorites</h4>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {favorites.map(preset => (
              <PresetCard
                key={preset.id}
                preset={preset}
                onToggleFavorite={handleToggleFavorite}
                onDelete={handleDelete}
                onDuplicate={handleDuplicate}
                onExport={handleExport}
              />
            ))}
          </div>
        </div>
      )}

      {/* All Presets */}
      <div className="space-y-3">
        <h4>All Presets</h4>
        <div className="grid grid-cols-2 gap-4">
          {regular.map(preset => (
            <PresetCard
              key={preset.id}
              preset={preset}
              onToggleFavorite={handleToggleFavorite}
              onDelete={handleDelete}
              onDuplicate={handleDuplicate}
              onExport={handleExport}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface PresetCardProps {
  preset: Preset;
  onToggleFavorite: (id: string) => void;
  onDelete: (id: string) => void;
  onDuplicate: (preset: Preset) => void;
  onExport: (preset: Preset) => void;
}

function PresetCard({ preset, onToggleFavorite, onDelete, onDuplicate, onExport }: PresetCardProps) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="truncate">{preset.name}</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggleFavorite(preset.id)}
              className="h-6 w-6 p-0"
            >
              <Star className={`w-4 h-4 ${preset.favorite ? 'fill-yellow-500 text-yellow-500' : ''}`} />
            </Button>
          </div>
          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
            {preset.description}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant="outline">{preset.workflow}</Badge>
        <Badge variant="secondary">{preset.usageCount} uses</Badge>
      </div>

      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-sm text-blue-500 hover:underline"
      >
        {showDetails ? 'Hide' : 'Show'} Parameters
      </button>

      {showDetails && (
        <div className="bg-muted/50 rounded-lg p-3 space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div>Steps: {preset.parameters.steps}</div>
            <div>CFG: {preset.parameters.cfg}</div>
            <div className="col-span-2">Sampler: {preset.parameters.sampler}</div>
            <div className="col-span-2">Scheduler: {preset.parameters.scheduler}</div>
            <div>Denoise: {preset.parameters.denoise}</div>
            <div>Seed: {preset.parameters.seed}</div>
          </div>
        </div>
      )}

      <div className="flex gap-2 pt-2 border-t border-border">
        <Button variant="outline" size="sm" className="flex-1">
          <Edit className="w-4 h-4 mr-2" />
          Load
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onDuplicate(preset)}>
          <Copy className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onExport(preset)}>
          <Download className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onDelete(preset.id)}>
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </Card>
  );
}
