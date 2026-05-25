import { Card } from './ui/card';
import { Button } from './ui/button';
import { Download, FileInput, RefreshCw, CheckCircle2 } from 'lucide-react';

export function QuickActions() {
  return (
    <Card className="p-6">
      <h3 className="mb-4">Quick Actions</h3>

      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" className="justify-start">
          <Download className="w-4 h-4 mr-2" />
          Download Missing
        </Button>

        <Button variant="outline" size="sm" className="justify-start">
          <CheckCircle2 className="w-4 h-4 mr-2" />
          Validate All
        </Button>

        <Button variant="outline" size="sm" className="justify-start">
          <FileInput className="w-4 h-4 mr-2" />
          Import Workflow
        </Button>

        <Button variant="outline" size="sm" className="justify-start">
          <RefreshCw className="w-4 h-4 mr-2" />
          Scan Directory
        </Button>
      </div>
    </Card>
  );
}
