import React, { useCallback } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Supervisor' },
    position: { x: 250, y: 50 },
    style: {
      fontFamily: "'CiscoSansTT'",
      border: '1px solid #0A60FF',
      backgroundColor: 'rgba(10, 96, 255, 0.3)',
      color: '#000000',
      fontWeight: '100',
      padding: 10,
      borderRadius: 5,
    },
  },
  {
    id: '2',
    type: 'output',
    data: { label: 'Sommelier' },
    position: { x: 250, y: 250 }, // Below the Exchange node
    style: {
      fontFamily: "'CiscoSansTT'",
      border: '1px solid #0A60FF',
      backgroundColor: 'rgba(10, 96, 255, 0.3)',
      color: '#000000',
      fontWeight: '100',
      padding: 10,
      borderRadius: 5,
    },
  },
];

const initialEdges = [
  {
    id: '1-2',
    source: '1',
    target: '2',
    label: 'SLIM',
    animated: true,
    style: { stroke: '#0A60FF', fontFamily: "'CiscoSansTT'", strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#0A60FF', // Change the color of the arrow
    },
  },
];

const proOptions = { hideAttribution: true };

const Graph = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <ReactFlowProvider>
      <div style={{ width: '100%', height: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          proOptions={proOptions}
          fitView
        >
          <Controls />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
};

export default Graph;
