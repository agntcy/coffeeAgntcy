import React, { useEffect } from 'react';
import {
    ReactFlow,
    ReactFlowProvider,
    useNodesState,
    useEdgesState,
    Controls,
    MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Constants for node and edge IDs
const NODE_IDS = {
    BUYER: '1',
    SOMMELIER: '2',
};

const EDGE_IDS = {
    BUYER_TO_SOMMELIER: '1-2',
};

// Initial nodes and edges
const initialNodes = [
    {
        id: NODE_IDS.BUYER,
        type: 'input',
        data: { label: 'Buyer' },
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
        id: NODE_IDS.SOMMELIER,
        type: 'output',
        data: { label: 'Sommelier' },
        position: { x: 250, y: 250 },
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
        id: EDGE_IDS.BUYER_TO_SOMMELIER,
        source: NODE_IDS.BUYER,
        target: NODE_IDS.SOMMELIER,
        label: 'A2A : SLIM',
        style: { stroke: '#0A60FF', fontFamily: "'CiscoSansTT'", strokeWidth: 2 },
        markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#0A60FF',
        },
    },
];

const Graph = ({ buttonClicked, setButtonClicked }) => {
    const [nodes, setNodes] = useNodesState(initialNodes);
    const [edges, setEdges] = useEdgesState(initialEdges);

    useEffect(() => {
        if (!buttonClicked) return;

        const animateGraph = async () => {
            const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

            // Change first node to green
            setNodes((nds) =>
                nds.map((node) =>
                    node.id === NODE_IDS.BUYER
                        ? {
                            ...node,
                            style: {
                                ...node.style,
                                backgroundColor: 'rgba(0, 255, 0, 0.3)',
                                border: '1px solid #00FF00',
                            },
                        }
                        : node
                )
            );
            await delay(300);

            // Reset to initial nodes
            setNodes(initialNodes);
            await delay(300);

            // Change edge to green
            setEdges((eds) =>
                eds.map((edge) =>
                    edge.id === EDGE_IDS.BUYER_TO_SOMMELIER
                        ? {
                            ...edge,
                            style: { ...edge.style, stroke: '#00FF00' },
                            markerEnd: { type: MarkerType.ArrowClosed, color: '#00FF00' },
                        }
                        : edge
                )
            );
            await delay(300);

            // Reset to initial edges
            setEdges(initialEdges);
            await delay(300);

            // Change second node to green
            setNodes((nds) =>
                nds.map((node) =>
                    node.id === NODE_IDS.SOMMELIER
                        ? {
                            ...node,
                            style: {
                                ...node.style,
                                backgroundColor: 'rgba(0, 255, 0, 0.3)',
                                border: '1px solid #00FF00',
                            },
                        }
                        : node
                )
            );
            await delay(300);

            // Reset to initial nodes
            setNodes(initialNodes);

            // Reset buttonClicked state
            setButtonClicked(false);
        };

        animateGraph();
    }, [buttonClicked, setButtonClicked]);

    return (
        <ReactFlowProvider>
            <div style={{ width: '100%', height: '100%' }}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    fitView
                >
                    <Controls />
                </ReactFlow>
            </div>
        </ReactFlowProvider>
    );
};

export default Graph;