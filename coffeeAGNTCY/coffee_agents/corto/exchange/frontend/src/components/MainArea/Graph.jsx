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
    Controls,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import CustomEdge from './Edge';

const DELAY_DURATION = 1000; // Duration for each animation step in milliseconds
const proOptions = { hideAttribution: true };

// Color constants
const COLORS = {
    NODE: {
        ORIGINAL: {
            BORDER: '#187ADC',
            BACKGROUND: 'rgba(24, 122, 220, 0.4)',
            TEXT: '#000000',
        },
        TRANSFER: {
            BORDER: '#00FF00',
            BACKGROUND: 'rgba(0, 255, 0, 0.4)',
        },
    },
    EDGE: {
        ORIGINAL: {
            STROKE: '#187ADC',
            LABEL_TEXT: '#FFFFFF',
            LABEL_BACKGROUND: '#187ADC',
        },
        TRANSFER: {
            STROKE: 'rgba(0, 255, 0, 0.4)',
            LABEL_TEXT: '#000000',
            LABEL_BACKGROUND: 'rgba(0, 255, 0, 0.7)',
        },
    },
};

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
            border: `1px solid ${COLORS.NODE.ORIGINAL.BORDER}`,
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
            color: COLORS.NODE.ORIGINAL.TEXT,
            fontWeight: '100',
            padding: 10,
            borderRadius: 5,
        },
    },
    {
        id: NODE_IDS.SOMMELIER,
        type: 'output',
        data: {
            label: (
                <div>
                    Sommelier
                    <div style={{ fontSize: '.65em' }}>
                        (Q Grader)
                    </div>
                </div>
            ),
        },
        position: { x: 250, y: 250 },
        style: {
            fontFamily: "'CiscoSansTT'",
            border: `1px solid ${COLORS.NODE.ORIGINAL.BORDER}`,
            backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
            color: COLORS.NODE.ORIGINAL.TEXT,
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
        style: { stroke: COLORS.EDGE.ORIGINAL.STROKE, strokeWidth: 2 },
        data: {
            label: 'A2A : SLIM',
            edgeColor: COLORS.EDGE.ORIGINAL.STROKE,
            labelColor: COLORS.EDGE.ORIGINAL.LABEL_TEXT,
            labelBackgroundColor: COLORS.EDGE.ORIGINAL.LABEL_BACKGROUND,
        },
        type: 'custom',
    },
];

const edgeTypes = {
    custom: CustomEdge,
};

const Graph = ({ buttonClicked, setButtonClicked }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    useEffect(() => {
        if (!buttonClicked) return;

        const animateGraph = async () => {
            const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

            // Change first node to TRANSFER color
            setNodes((nds) =>
                nds.map((node) =>
                    node.id === NODE_IDS.BUYER
                        ? {
                            ...node,
                            style: {
                                ...node.style,
                                backgroundColor: COLORS.NODE.TRANSFER.BACKGROUND,
                                border: `1px solid ${COLORS.NODE.TRANSFER.BORDER}`,
                            },
                        }
                        : node
                )
            );
            await delay(DELAY_DURATION);

            // Change edge to TRANSFER color
            setEdges((eds) =>
                eds.map((edge) =>
                    edge.id === EDGE_IDS.BUYER_TO_SOMMELIER
                        ? {
                            ...edge,
                            style: { ...edge.style, stroke: COLORS.EDGE.TRANSFER.STROKE },
                            data: {
                                ...edge.data,
                                edgeColor: COLORS.EDGE.TRANSFER.STROKE,
                                labelColor: COLORS.EDGE.TRANSFER.LABEL_TEXT,
                                labelBackgroundColor: COLORS.EDGE.TRANSFER.LABEL_BACKGROUND,
                            },
                        }
                        : edge
                )
            );
            await delay(DELAY_DURATION);

            // Change second node to TRANSFER color
            setNodes((nds) =>
                nds.map((node) =>
                    node.id === NODE_IDS.SOMMELIER
                        ? {
                            ...node,
                            style: {
                                ...node.style,
                                backgroundColor: COLORS.NODE.TRANSFER.BACKGROUND,
                                border: `1px solid ${COLORS.NODE.TRANSFER.BORDER}`,
                            },
                        }
                        : node
                )
            );
            await delay(DELAY_DURATION);

            // Reset nodes and edges to initial state
            setNodes((nds) =>
                nds.map((node) => ({
                    ...node,
                    style: initialNodes.find((n) => n.id === node.id).style,
                    position: node.position, // Ensure position remains unchanged
                }))
            );
            setEdges(initialEdges);

            // Reset buttonClicked state
            setButtonClicked(false);
        };

        animateGraph();
    }, [buttonClicked, setButtonClicked]);

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                proOptions={proOptions}
                edgeTypes={edgeTypes}
                fitView
            >
                <Controls />
            </ReactFlow>
        </div>
    );
};

// Wrapping with ReactFlowProvider
function FlowWithProvider(props) {
    return (
        <ReactFlowProvider>
            <Graph {...props} />
        </ReactFlowProvider>
    );
}

export default FlowWithProvider;