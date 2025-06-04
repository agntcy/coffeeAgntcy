/**
 * Copyright 2025 Cisco Systems, Inc. and its affiliates
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect } from 'react';
import {
    ReactFlow,
    ReactFlowProvider,
    useNodesState,
    useEdgesState,
    MarkerType,
    Controls,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import SlimNode from './SlimNode';

// Node types
const nodeTypes = {
    slimNode: SlimNode,
};

// Constants
const DELAY_DURATION = 1000; // Animation delay in milliseconds
const proOptions = { hideAttribution: true };

// Colors
const COLORS = {
    NODE: {
        ORIGINAL: { BORDER: '#187ADC', BACKGROUND: 'rgba(24, 122, 220, 0.4)', TEXT: '#000000' },
        TRANSFER: { BORDER: '#00FF00', BACKGROUND: 'rgba(0, 255, 0, 0.4)' },
    },
    EDGE: {
        ORIGINAL: { STROKE: '#187ADC' },
        TRANSFER: { STROKE: 'rgba(0, 255, 0, 0.4)' },
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

const EDGE_IDS = {
    BUYER_TO_SLIM: '1-2',
    SLIM_TO_BRAZIL: '2-3',
    SLIM_TO_COLOMBIA: '2-4',
    COLOMBIA_TO_COFFEE_FARM_SITE: '4-5',
    SLIM_TO_TATOUINE: '2-6',
};

// Common node style
const commonNodeStyle = {
    fontFamily: "'CiscoSansTT'",
    border: `1px solid ${COLORS.NODE.ORIGINAL.BORDER}`,
    backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
    color: COLORS.NODE.ORIGINAL.TEXT,
    fontWeight: '100',
    padding: 10,
    borderRadius: 5,
};

// Initial nodes
const initialNodes = [
    { id: NODE_IDS.BUYER, type: 'input', data: { label: 'Buyer' }, position: { x: 300, y: 100 }, style: commonNodeStyle },
    { id: NODE_IDS.SLIM, data: { label: 'Pub/Sub(SLIM)' }, position: { x: 60, y: 250 }, type: 'slimNode' },
    { id: NODE_IDS.BRAZIL, type: 'output', data: { label: 'Brazil' }, position: { x: 100, y: 450 }, style: commonNodeStyle },
    { id: NODE_IDS.COLOMBIA, type: 'default', data: { label: 'Colombia' }, position: { x: 300, y: 450 }, style: commonNodeStyle },
    { id: NODE_IDS.TATOUINE, type: 'output', data: { label: 'Tatouine' }, position: { x: 500, y: 450 }, style: commonNodeStyle },
    { id: NODE_IDS.COFFEE_FARM_SITE, type: 'output', data: { label: 'Weather' }, position: { x: 300, y: 600 }, style: commonNodeStyle },
];

// Helper to apply markers to edges
const applyMarkers = (edge, color) => ({
    ...edge,
    markerStart: { type: MarkerType.ArrowClosed, color },
    markerEnd: { type: MarkerType.ArrowClosed, color },
});

// Initial edges
const initialEdges = [
    applyMarkers(
        {
            id: EDGE_IDS.BUYER_TO_SLIM,
            source: NODE_IDS.BUYER,
            target: NODE_IDS.SLIM,
            sourceHandle: null,
            targetHandle: 'top',
            style: { stroke: COLORS.EDGE.ORIGINAL.STROKE, strokeWidth: 2 },
            label: 'A2A',
        },
        COLORS.EDGE.ORIGINAL.STROKE
    ),
    applyMarkers(
        {
            id: EDGE_IDS.SLIM_TO_BRAZIL,
            source: NODE_IDS.SLIM,
            target: NODE_IDS.BRAZIL,
            sourceHandle: 'a',
            style: { stroke: COLORS.EDGE.ORIGINAL.STROKE, strokeWidth: 2 },
            label: 'A2A',
        },
        COLORS.EDGE.ORIGINAL.STROKE
    ),
    applyMarkers(
        {
            id: EDGE_IDS.SLIM_TO_COLOMBIA,
            source: NODE_IDS.SLIM,
            target: NODE_IDS.COLOMBIA,
            sourceHandle: 'b',
            style: { stroke: COLORS.EDGE.ORIGINAL.STROKE, strokeWidth: 2 },
            label: 'A2A',
        },
        COLORS.EDGE.ORIGINAL.STROKE
    ),
    applyMarkers(
        {
            id: EDGE_IDS.COLOMBIA_TO_COFFEE_FARM_SITE,
            source: NODE_IDS.COLOMBIA,
            target: NODE_IDS.COFFEE_FARM_SITE,
            sourceHandle: null,
            targetHandle: null,
            style: { stroke: COLORS.EDGE.ORIGINAL.STROKE, strokeWidth: 2 },
            label: 'MCP',
        },
        COLORS.EDGE.ORIGINAL.STROKE
    ),
    applyMarkers(
        {
            id: EDGE_IDS.SLIM_TO_TATOUINE,
            source: NODE_IDS.SLIM,
            target: NODE_IDS.TATOUINE,
            sourceHandle: 'c',
            targetHandle: null,
            style: { stroke: COLORS.EDGE.ORIGINAL.STROKE, strokeWidth: 2 },
            label: 'A2A',
        },
        COLORS.EDGE.ORIGINAL.STROKE
    ),
];

// Graph component
const Graph = ({ buttonClicked, setButtonClicked }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    // Helper: Delay function
    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    // Helper: Update node style
    const updateNodeStyle = (nodeId, backgroundColor, borderColor) => {
        setNodes((nds) =>
            nds.map((node) =>
                node.id === nodeId
                    ? { ...node, style: { ...node.style, backgroundColor, border: `1px solid ${borderColor}` } }
                    : node
            )
        );
    };

    // Helper: Update edge style
    const updateEdgeStyle = (edgeId, strokeColor) => {
        setEdges((eds) =>
            eds.map((edge) =>
                edge.id === edgeId
                    ? { ...edge, style: { ...edge.style, stroke: strokeColor }, markerStart: { type: MarkerType.ArrowClosed, color: strokeColor }, markerEnd: { type: MarkerType.ArrowClosed, color: strokeColor } }
                    : edge
            )
        );
    };

    // Animation logic
    useEffect(() => {
        if (!buttonClicked) return;

        const animateGraph = async () => {
            // Step 1: Highlight Buyer node
            updateNodeStyle(NODE_IDS.BUYER, COLORS.NODE.TRANSFER.BACKGROUND, COLORS.NODE.TRANSFER.BORDER);
            await delay(DELAY_DURATION);

            // Step 2: Highlight Buyer to SLIM edge
            updateEdgeStyle(EDGE_IDS.BUYER_TO_SLIM, COLORS.EDGE.TRANSFER.STROKE);
            await delay(DELAY_DURATION);

            // Step 3: Highlight SLIM to country edges and nodes
            [EDGE_IDS.SLIM_TO_BRAZIL, EDGE_IDS.SLIM_TO_COLOMBIA, EDGE_IDS.SLIM_TO_TATOUINE].forEach((edgeId) =>
                updateEdgeStyle(edgeId, COLORS.EDGE.TRANSFER.STROKE)
            );
            [NODE_IDS.BRAZIL, NODE_IDS.COLOMBIA, NODE_IDS.TATOUINE].forEach((nodeId) =>
                updateNodeStyle(nodeId, COLORS.NODE.TRANSFER.BACKGROUND, COLORS.NODE.TRANSFER.BORDER)
            );
            await delay(DELAY_DURATION);

            // Step 4: Highlight Colombia to Coffee Farm Site edge and node
            updateEdgeStyle(EDGE_IDS.COLOMBIA_TO_COFFEE_FARM_SITE, COLORS.EDGE.TRANSFER.STROKE);
            await delay(DELAY_DURATION);
            updateNodeStyle(NODE_IDS.COFFEE_FARM_SITE, COLORS.NODE.TRANSFER.BACKGROUND, COLORS.NODE.TRANSFER.BORDER);
            await delay(DELAY_DURATION);

            // Reset to initial state
            setNodes(initialNodes);
            setEdges(initialEdges);
            setButtonClicked(false);
        };

        animateGraph();
    }, [buttonClicked, setButtonClicked]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
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

// Wrapper with ReactFlowProvider
const FlowWithProvider = (props) => (
    <ReactFlowProvider>
        <Graph {...props} />
    </ReactFlowProvider>
);

export default FlowWithProvider;
