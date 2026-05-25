import { Keyboard } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  { keys: ['Ctrl', 'K'], description: 'Focus search', category: 'Navigation' },
  { keys: ['Ctrl', 'M'], description: 'Switch to Models tab', category: 'Navigation' },
  { keys: ['Ctrl', 'W'], description: 'Switch to Workflows tab', category: 'Navigation' },
  { keys: ['Ctrl', 'D'], description: 'Switch to Dependencies tab', category: 'Navigation' },
  { keys: ['Ctrl', 'Shift', 'A'], description: 'Toggle Advanced Features', category: 'Navigation' },
  { keys: ['Ctrl', 'Shift', 'S'], description: 'Open ComfyWatchman', category: 'Navigation' },
  { keys: ['Ctrl', 'E'], description: 'Export data', category: 'Actions' },
  { keys: ['?'], description: 'Show keyboard shortcuts', category: 'Help' },
  { keys: ['Esc'], description: 'Close dialogs/modals', category: 'General' },
];

export function KeyboardShortcutsDialog() {
  const categories = Array.from(new Set(shortcuts.map(s => s.category)));

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <Keyboard className="w-4 h-4 mr-2" />
          Shortcuts
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Boost your productivity with these keyboard shortcuts
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {categories.map(category => (
            <div key={category}>
              <h4 className="mb-3 text-muted-foreground">{category}</h4>
              <div className="space-y-2">
                {shortcuts
                  .filter(s => s.category === category)
                  .map((shortcut, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between py-2 border-b border-border last:border-0"
                    >
                      <span className="text-sm">{shortcut.description}</span>
                      <div className="flex gap-1">
                        {shortcut.keys.map((key, i) => (
                          <kbd
                            key={i}
                            className="px-2 py-1 text-xs rounded bg-muted border border-border"
                          >
                            {key}
                          </kbd>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
