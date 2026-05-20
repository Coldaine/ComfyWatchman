import { useState } from 'react';
import { Download, Upload, FileJson, CheckCircle2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { comfyUIService } from '../services/comfyui-service';
import { toast } from 'sonner@2.0.3';

export function ExportImportDialog() {
  const [exportType, setExportType] = useState<'models' | 'workflows' | 'all'>('all');
  const [exportedData, setExportedData] = useState<string>('');
  const [importData, setImportData] = useState<string>('');
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      const data = await comfyUIService.exportData(exportType);
      setExportedData(data);

      // Auto-download
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comfyui-${exportType}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('Data exported successfully');
    } catch (error) {
      toast.error('Failed to export data');
      console.error('Export error:', error);
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async () => {
    try {
      setImporting(true);
      const result = await comfyUIService.importData(importData);

      toast.success(
        `Imported ${result.models} models and ${result.workflows} workflows`
      );

      setImportData('');
    } catch (error) {
      toast.error('Failed to import data. Please check the JSON format.');
      console.error('Import error:', error);
    } finally {
      setImporting(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setImportData(content);
      };
      reader.readAsText(file);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(exportedData);
    toast.success('Copied to clipboard');
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <FileJson className="w-4 h-4 mr-2" />
          Export/Import
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Export & Import Data</DialogTitle>
          <DialogDescription>
            Backup your models and workflows or import from another instance
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="export" className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="export">
              <Download className="w-4 h-4 mr-2" />
              Export
            </TabsTrigger>
            <TabsTrigger value="import">
              <Upload className="w-4 h-4 mr-2" />
              Import
            </TabsTrigger>
          </TabsList>

          <TabsContent value="export" className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label>What to export</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <Button
                    variant={exportType === 'models' ? 'default' : 'outline'}
                    onClick={() => setExportType('models')}
                    size="sm"
                  >
                    Models Only
                  </Button>
                  <Button
                    variant={exportType === 'workflows' ? 'default' : 'outline'}
                    onClick={() => setExportType('workflows')}
                    size="sm"
                  >
                    Workflows Only
                  </Button>
                  <Button
                    variant={exportType === 'all' ? 'default' : 'outline'}
                    onClick={() => setExportType('all')}
                    size="sm"
                  >
                    Everything
                  </Button>
                </div>
              </div>

              <Button onClick={handleExport} disabled={exporting} className="w-full">
                <Download className="w-4 h-4 mr-2" />
                {exporting ? 'Exporting...' : 'Export Data'}
              </Button>

              {exportedData && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Exported Data</Label>
                    <Button variant="ghost" size="sm" onClick={copyToClipboard}>
                      Copy to Clipboard
                    </Button>
                  </div>
                  <Textarea
                    value={exportedData}
                    readOnly
                    className="h-64 font-mono text-xs"
                  />
                  <div className="flex items-center gap-2 text-sm text-green-500">
                    <CheckCircle2 className="w-4 h-4" />
                    Data exported and downloaded successfully
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="import" className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label>Upload JSON File</Label>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="mt-2 block w-full text-sm text-muted-foreground
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-md file:border-0
                    file:bg-primary file:text-primary-foreground
                    hover:file:bg-primary/90
                    file:cursor-pointer cursor-pointer"
                />
              </div>

              <div>
                <Label>Or Paste JSON Data</Label>
                <Textarea
                  value={importData}
                  onChange={(e) => setImportData(e.target.value)}
                  placeholder="Paste your exported JSON data here..."
                  className="h-64 font-mono text-xs mt-2"
                />
              </div>

              <div className="bg-muted p-3 rounded-md">
                <p className="text-sm text-muted-foreground">
                  <strong>Note:</strong> Importing will merge data with your existing collection.
                  Duplicate entries will be skipped.
                </p>
              </div>

              <Button
                onClick={handleImport}
                disabled={!importData || importing}
                className="w-full"
              >
                <Upload className="w-4 h-4 mr-2" />
                {importing ? 'Importing...' : 'Import Data'}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
