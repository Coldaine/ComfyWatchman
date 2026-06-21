import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { BatchOperations } from './BatchOperations';
import { DownloadQueue } from './DownloadQueue';
import { DragDropManager } from './DragDropManager';
import { ParameterPresets } from './ParameterPresets';
import { SmartRecommendations } from './SmartRecommendations';
import { Model, Workflow } from '../types';
import {
  CheckSquare,
  Download,
  GripVertical,
  Settings,
  Sparkles
} from 'lucide-react';

interface AdvancedFeaturesProps {
  models: Model[];
  workflows: Workflow[];
}

export function AdvancedFeatures({ models, workflows }: AdvancedFeaturesProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1>Advanced Features</h1>
        <p className="text-muted-foreground mt-1">
          Powerful tools for managing your ComfyUI workspace
        </p>
      </div>

      <Tabs defaultValue="batch" className="space-y-6">
        <TabsList>
          <TabsTrigger value="batch" className="gap-2">
            <CheckSquare className="w-4 h-4" />
            Batch Operations
          </TabsTrigger>
          <TabsTrigger value="downloads" className="gap-2">
            <Download className="w-4 h-4" />
            Download Queue
          </TabsTrigger>
          <TabsTrigger value="dragdrop" className="gap-2">
            <GripVertical className="w-4 h-4" />
            Drag & Drop
          </TabsTrigger>
          <TabsTrigger value="presets" className="gap-2">
            <Settings className="w-4 h-4" />
            Parameter Presets
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="gap-2">
            <Sparkles className="w-4 h-4" />
            Recommendations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="batch">
          <BatchOperations models={models} />
        </TabsContent>

        <TabsContent value="downloads">
          <DownloadQueue />
        </TabsContent>

        <TabsContent value="dragdrop">
          <DragDropManager workflows={workflows} />
        </TabsContent>

        <TabsContent value="presets">
          <ParameterPresets />
        </TabsContent>

        <TabsContent value="recommendations">
          <SmartRecommendations />
        </TabsContent>
      </Tabs>
    </div>
  );
}
