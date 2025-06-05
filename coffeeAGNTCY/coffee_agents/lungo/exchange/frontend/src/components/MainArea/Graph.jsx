import React, { useEffect, useRef } from 'react';
import {
    ReactFlow,
    ReactFlowProvider,
    useNodesState,
    useEdgesState,
    Controls,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { FaUserTie, FaWarehouse, FaCloudSun } from 'react-icons/fa';
import SlimNode from './SlimNode';
import CustomEdge from './CustomEdge';
import CustomNode from './CustomNode';

const proOptions = { hideAttribution: true };

// Node types
const nodeTypes = {
    slimNode: SlimNode,
    customNode: CustomNode,
};

// Constants
const DELAY_DURATION = 1750; // Animation delay in milliseconds

// Colors
const COLORS = {
    NODE: {
        ORIGINAL: { BACKGROUND: '#F5F5F5' },
        TRANSFER: { BACKGROUND: 'rgba(255, 223, 0, 0.4)' },
    },
};

// Node and Edge IDs
const NODE_IDS = {
    BUYER: '1',
    SLIM: '2',
    BRAZIL: '3',
    COLOMBIA: '4',
    COFFEE_FARM_SITE: '5',
    TATOUINE: '6',
};

const initialNodes = [
    {
        id: NODE_IDS.BUYER,
        type: 'customNode',
        data: {
            icon: <FaUserTie />,
            label1: 'Supervisor Agent',
            label2: 'Buyer',
            handles: 'source',
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
        },
        position: { x: 300, y: 100 },
    },
    {
        id: NODE_IDS.SLIM,
        type: 'slimNode',
        data: {
            label: 'Pub/Sub (SLIM)',
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
        },
        position: { x: 60, y: 250 },
    },
    {
        id: NODE_IDS.BRAZIL,
        type: 'customNode',
        data: {
            icon: <FaWarehouse />,
            label1: 'Coffee Farm Agent',
            label2: 'Brazil',
            handles: 'target',
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
        },
        position: { x: 93, y: 450 },
    },
    {
        id: NODE_IDS.COLOMBIA,
        type: 'customNode',
        data: {
            icon: <FaWarehouse />,
            label1: 'Coffee Farm Agent',
            label2: 'Colombia',
            handles: 'all',
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
        },
        position: { x: 303, y: 450 },
    },
    {
        id: NODE_IDS.TATOUINE,
        type: 'customNode',
        data: {
            icon: <FaWarehouse />,
            label1: 'Coffee Farm Agent',
            label2: 'Tatouine',
            handles: 'target',
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
        },
        position: { x: 512, y: 450 },
    },
    {
        id: NODE_IDS.COFFEE_FARM_SITE,
        type: 'customNode',
        data: {
            icon: <FaCloudSun />,
            label1: 'MCP Server',
            label2: 'Weather',
            handles: 'target',
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
        },
        position: { x: 303, y: 650 },
    },
];

const edgeTypes = {
    custom: CustomEdge,
};

const initialEdges = [
    {
        id: '1-2',
        source: NODE_IDS.BUYER,
        target: NODE_IDS.SLIM,
        targetHandle: 'top',
        style: { stroke: '#187ADC', strokeWidth: 2 },
        data: { label: 'A2A', labelIconType: 'google' },
        type: 'custom',
    },
    {
        id: '2-3',
        source: NODE_IDS.SLIM,
        target: NODE_IDS.BRAZIL,
        sourceHandle: 'bottom_left',
        style: { stroke: '#187ADC', strokeWidth: 2 },
        data: { label: 'A2A', labelIconType: 'google' },
        type: 'custom',
    },
    {
        id: '2-4',
        source: NODE_IDS.SLIM,
        target: NODE_IDS.COLOMBIA,
        sourceHandle: 'bottom_center',
        style: { stroke: '#187ADC', strokeWidth: 2 },
        data: { label: 'A2A', labelIconType: 'google' },
        type: 'custom',
    },
    {
        id: '4-5',
        source: NODE_IDS.COLOMBIA,
        target: NODE_IDS.COFFEE_FARM_SITE,
        style: { stroke: '#187ADC', strokeWidth: 2 },
        data: { label: 'MCP', labelIconType: 'mcp' },
        type: 'custom',
    },
    {
        id: '2-6',
        source: NODE_IDS.SLIM,
        target: NODE_IDS.TATOUINE,
        sourceHandle: 'bottom_right',
        style: { stroke: '#187ADC', strokeWidth: 2 },
        data: { label: 'A2A', labelIconType: 'google' },
        type: 'custom',
    },
];

const Graph = ({ buttonClicked, setButtonClicked, aiReplied, setAiReplied }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const animationLock = useRef(false); // Lock to prevent overlapping animations

    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    const updateNodeStyle = (nodeId, backgroundColor) => {
        setNodes((nds) =>
            nds.map((node) =>
                node.id === nodeId && node.type === 'customNode'
                    ? { ...node, data: { ...node.data, backgroundColor } }
                    : node
            )
        );
    };

    useEffect(() => {
        if (!buttonClicked && !aiReplied) return;
        if (animationLock.current) return; // Prevent overlapping animations
        animationLock.current = true;

        const animateNode = async (nodeIds, color) => {
            nodeIds.forEach((nodeId) => updateNodeStyle(nodeId, color));
            await delay(DELAY_DURATION);
        };

        const getRandomInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;

        const animateGraph = async () => {
            if (!aiReplied) {
                // Forward animation
                await animateNode([NODE_IDS.BUYER], COLORS.NODE.TRANSFER.BACKGROUND);
                await animateNode([NODE_IDS.BUYER], COLORS.NODE.ORIGINAL.BACKGROUND);

                await animateNode([NODE_IDS.BRAZIL, NODE_IDS.COLOMBIA, NODE_IDS.TATOUINE], COLORS.NODE.TRANSFER.BACKGROUND);
                await animateNode([NODE_IDS.BRAZIL, NODE_IDS.COLOMBIA, NODE_IDS.TATOUINE], COLORS.NODE.ORIGINAL.BACKGROUND);

                await animateNode([NODE_IDS.COFFEE_FARM_SITE], COLORS.NODE.TRANSFER.BACKGROUND);
                await animateNode([NODE_IDS.COFFEE_FARM_SITE], COLORS.NODE.ORIGINAL.BACKGROUND);
            } else {
                // Backward animation
                const randomPropagation = getRandomInt(0, 2);
                switch (randomPropagation) {
                    case 0: // Backward propagation starting from MCP
                        await animateNode([NODE_IDS.COFFEE_FARM_SITE], COLORS.NODE.TRANSFER.BACKGROUND);
                        await animateNode([NODE_IDS.COFFEE_FARM_SITE], COLORS.NODE.ORIGINAL.BACKGROUND);
                        await animateNode([NODE_IDS.COLOMBIA], COLORS.NODE.TRANSFER.BACKGROUND);
                        await animateNode([NODE_IDS.COLOMBIA], COLORS.NODE.ORIGINAL.BACKGROUND);
                        break;
                    case 1: // Backward propagation starting from Brazil
                        await animateNode([NODE_IDS.BRAZIL], COLORS.NODE.TRANSFER.BACKGROUND);
                        await animateNode([NODE_IDS.BRAZIL], COLORS.NODE.ORIGINAL.BACKGROUND);
                        break;
                    case 2: // Backward propagation starting from Tatouine
                        await animateNode([NODE_IDS.TATOUINE], COLORS.NODE.TRANSFER.BACKGROUND);
                        await animateNode([NODE_IDS.TATOUINE], COLORS.NODE.ORIGINAL.BACKGROUND);
                        break;
                }

                await animateNode([NODE_IDS.BUYER], COLORS.NODE.TRANSFER.BACKGROUND);
                await animateNode([NODE_IDS.BUYER], COLORS.NODE.ORIGINAL.BACKGROUND);
                setAiReplied(false);
            }

            setButtonClicked(false);
            animationLock.current = false; // Release the lock
        };

        animateGraph();
    }, [buttonClicked, setButtonClicked, aiReplied]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                proOptions={proOptions}
                fitView
            >
                <Controls />
            </ReactFlow>
        </div>
    );
};

const FlowWithProvider = (props) => (
    <ReactFlowProvider>
        <Graph {...props} />
    </ReactFlowProvider>
);

export default FlowWithProvider;