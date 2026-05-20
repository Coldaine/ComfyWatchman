import { useState } from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Workflow } from '../types';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { GripVertical, Workflow as WorkflowIcon } from 'lucide-react';
import { toast } from 'sonner@2.0.3';

interface DraggableWorkflowProps {
  workflow: Workflow;
  index: number;
  moveWorkflow: (dragIndex: number, hoverIndex: number) => void;
}

const DraggableWorkflow = ({ workflow, index, moveWorkflow }: DraggableWorkflowProps) => {
  const [{ isDragging }, drag, preview] = useDrag({
    type: 'workflow',
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: 'workflow',
    hover: (item: { index: number }) => {
      if (item.index !== index) {
        moveWorkflow(item.index, index);
        item.index = index;
      }
    },
  });

  return (
    <div ref={(node) => preview(drop(node))} style={{ opacity: isDragging ? 0.5 : 1 }}>
      <Card className="p-4 cursor-move transition-all hover:border-primary">
        <div className="flex items-center gap-4">
          <div ref={drag} className="cursor-grab active:cursor-grabbing">
            <GripVertical className="w-5 h-5 text-muted-foreground" />
          </div>

          <WorkflowIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="truncate">{workflow.name}</h4>
              {workflow.status === 'ready' ? (
                <Badge variant="outline" className="text-green-500 border-green-500">
                  Ready
                </Badge>
              ) : (
                <Badge variant="destructive">Missing Models</Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground truncate mt-1">
              {workflow.description}
            </p>
          </div>

          <div className="text-sm text-muted-foreground">
            Position: {index + 1}
          </div>
        </div>
      </Card>
    </div>
  );
};

interface DragDropManagerProps {
  workflows: Workflow[];
}

export function DragDropManager({ workflows: initialWorkflows }: DragDropManagerProps) {
  const [workflows, setWorkflows] = useState(initialWorkflows);

  const moveWorkflow = (dragIndex: number, hoverIndex: number) => {
    const draggedWorkflow = workflows[dragIndex];
    const newWorkflows = [...workflows];
    newWorkflows.splice(dragIndex, 1);
    newWorkflows.splice(hoverIndex, 0, draggedWorkflow);
    setWorkflows(newWorkflows);
  };

  const handleSaveOrder = () => {
    toast.success('Workflow order saved successfully');
    console.log('New order:', workflows.map(w => w.name));
  };

  const handleResetOrder = () => {
    setWorkflows(initialWorkflows);
    toast.success('Workflow order reset to default');
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="space-y-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3>Drag & Drop Workflow Manager</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Drag workflows to reorder them. Changes are saved automatically.
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleResetOrder}
                className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
              >
                Reset Order
              </button>
              <button
                onClick={handleSaveOrder}
                className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                Save Order
              </button>
            </div>
          </div>
        </Card>

        <div className="space-y-3">
          {workflows.map((workflow, index) => (
            <DraggableWorkflow
              key={workflow.id}
              workflow={workflow}
              index={index}
              moveWorkflow={moveWorkflow}
            />
          ))}
        </div>
      </div>
    </DndProvider>
  );
}
