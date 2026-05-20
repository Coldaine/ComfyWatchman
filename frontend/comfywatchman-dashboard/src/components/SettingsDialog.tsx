import { Settings, RotateCcw } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { useUserPreferences } from '../hooks/useUserPreferences';
import { toast } from 'sonner@2.0.3';

export function SettingsDialog() {
  const { preferences, updatePreference, resetPreferences } = useUserPreferences();

  const handleReset = () => {
    resetPreferences();
    toast.success('Settings reset to defaults');
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <Settings className="w-4 h-4 mr-2" />
          Settings
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Customize your dashboard experience
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Display Preferences */}
          <div className="space-y-4">
            <h4>Display Preferences</h4>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Default Tab</Label>
                <Select
                  value={preferences.defaultTab}
                  onValueChange={(value: any) => updatePreference('defaultTab', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="models">Models</SelectItem>
                    <SelectItem value="workflows">Workflows</SelectItem>
                    <SelectItem value="dependencies">Dependencies</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Default Sort</Label>
                <Select
                  value={preferences.defaultSortBy}
                  onValueChange={(value: any) => updatePreference('defaultSortBy', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="name">Name</SelectItem>
                    <SelectItem value="size">Size</SelectItem>
                    <SelectItem value="date">Date Added</SelectItem>
                    <SelectItem value="usage">Usage</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Compact Mode</Label>
                <div className="text-sm text-muted-foreground">
                  Show more items with less spacing
                </div>
              </div>
              <Switch
                checked={preferences.compactMode}
                onCheckedChange={(checked) => updatePreference('compactMode', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Show Missing Models Alert</Label>
                <div className="text-sm text-muted-foreground">
                  Display alert banner for missing models
                </div>
              </div>
              <Switch
                checked={preferences.showMissingModelsAlert}
                onCheckedChange={(checked) => updatePreference('showMissingModelsAlert', checked)}
              />
            </div>
          </div>

          <Separator />

          {/* Behavior Preferences */}
          <div className="space-y-4">
            <h4>Behavior</h4>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto Refresh</Label>
                <div className="text-sm text-muted-foreground">
                  Automatically refresh data every {preferences.autoRefreshInterval} seconds
                </div>
              </div>
              <Switch
                checked={preferences.autoRefresh}
                onCheckedChange={(checked) => updatePreference('autoRefresh', checked)}
              />
            </div>

            {preferences.autoRefresh && (
              <div className="space-y-2 ml-4">
                <Label>Refresh Interval (seconds)</Label>
                <Select
                  value={preferences.autoRefreshInterval.toString()}
                  onValueChange={(value) => updatePreference('autoRefreshInterval', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 seconds</SelectItem>
                    <SelectItem value="30">30 seconds</SelectItem>
                    <SelectItem value="60">1 minute</SelectItem>
                    <SelectItem value="300">5 minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Confirm Delete</Label>
                <div className="text-sm text-muted-foreground">
                  Show confirmation dialog before deleting items
                </div>
              </div>
              <Switch
                checked={preferences.confirmDelete}
                onCheckedChange={(checked) => updatePreference('confirmDelete', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Keyboard Shortcuts</Label>
                <div className="text-sm text-muted-foreground">
                  Enable keyboard shortcuts for quick actions
                </div>
              </div>
              <Switch
                checked={preferences.enableKeyboardShortcuts}
                onCheckedChange={(checked) => updatePreference('enableKeyboardShortcuts', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Real-time Updates</Label>
                <div className="text-sm text-muted-foreground">
                  Enable live updates for download progress and activity
                </div>
              </div>
              <Switch
                checked={preferences.enableRealTimeUpdates}
                onCheckedChange={(checked) => updatePreference('enableRealTimeUpdates', checked)}
              />
            </div>
          </div>

          <Separator />

          {/* Export/Import Defaults */}
          <div className="space-y-4">
            <h4>Export/Import</h4>

            <div className="space-y-2">
              <Label>Default Export Type</Label>
              <Select
                value={preferences.defaultExportType}
                onValueChange={(value: any) => updatePreference('defaultExportType', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="models">Models Only</SelectItem>
                  <SelectItem value="workflows">Workflows Only</SelectItem>
                  <SelectItem value="all">Everything</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          {/* Reset */}
          <div className="flex items-center justify-between pt-4">
            <div className="space-y-0.5">
              <Label>Reset Settings</Label>
              <div className="text-sm text-muted-foreground">
                Restore all settings to their default values
              </div>
            </div>
            <Button variant="outline" onClick={handleReset}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
