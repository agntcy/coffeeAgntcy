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
import { EdgeLabelIcon } from '../../utils/const.js';

const proOptions = { hideAttribution: true };

// Node types
const nodeTypes = {
    slimNode: SlimNode,
    customNode: CustomNode,
};

// Constants
const DELAY_DURATION = 1000; // Animation delay in milliseconds

// Colors
const COLORS = {
    NODE: {
        ORIGINAL: { BACKGROUND: '#F5F5F5' },
    },
};

const HIGHLIGHT = {
    ON: true,
    OFF: false,
};

// Node and Edge IDs
const NODE_IDS = {
    BUYER: '1',
    SLIM: '2',
    SOMMELIER: '3',
};

const EDGE_IDS = {
    BUYER_TO_SLIM: '1-2',
    SLIM_TO_SOMMELIER: '2-3',
};

// Initial nodes
const commonNodeData = {
    backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
};


/*
Node ID: 1, Position: X=529.1332569384248, Y=159.4805787605829
Graph.jsx:151 Node ID: 2, Position: X=512.0237044953464, Y=368.688426426175
Graph.jsx:151 Node ID: 3, Position: X=534.0903941835277, Y=582.9317472571444
 */
const initialNodes = [
    {
        id: NODE_IDS.BUYER,
        type: 'customNode',
        data: {
            ...commonNodeData,
            icon: <FaUserTie />,
            label1: 'Supervisor Agent',
            label2: 'Buyer',
            handles: 'source',
        },
        position: { x: 529.1332569384248, y: 159.4805787605829 },
    },
    {
        id: NODE_IDS.SLIM,
        type: 'slimNode',
        data: {
            ...commonNodeData,
            label: 'SLIM',
        },
        position: { x: 512.0237044953464, y: 368.688426426175 },
    },
    {
        id: NODE_IDS.SOMMELIER,
        type: 'customNode',
        data: {
            ...commonNodeData,
            icon: <FaWarehouse />,
            label1: 'Q Grader Agent',
            label2: 'Sommelier',
            handles: 'target',
        },
        position: { x: 534.0903941835277, y: 582.9317472571444 },
    },
];

// Edge types
const edgeTypes = {
    custom: CustomEdge,
};

// Initial edges
const initialEdges = [
    {
        id: EDGE_IDS.BUYER_TO_SLIM,
        source: NODE_IDS.BUYER,
        target: NODE_IDS.SLIM,
        targetHandle: 'top',
        data: { label: 'A2A', labelIconType: EdgeLabelIcon.A2A },
        type: 'custom',
    },
    {
        id: EDGE_IDS.SLIM_TO_SOMMELIER,
        source: NODE_IDS.SLIM,
        target: NODE_IDS.SOMMELIER,
        sourceHandle: 'bottom_center',
        data: { label: 'A2A', labelIconType: EdgeLabelIcon.A2A },
        type: 'custom',
    },
    {
        id: EDGE_IDS.SLIM_TO_COLOMBIA,
        source: NODE_IDS.SLIM,
        target: NODE_IDS.COLOMBIA,
        sourceHandle: 'bottom_center',
        data: { label: 'A2A', labelIconType: EdgeLabelIcon.A2A },
        type: 'custom',
    },
];

const Graph = ({ buttonClicked, setButtonClicked, aiReplied, setAiReplied }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const animationLock = useRef(false); // Lock to prevent overlapping animations

    useEffect(() => {
        if (nodes) {
            nodes.forEach((node) => {
                console.log(`Node ID: ${node.id}, Position: X=${node.position.x}, Y=${node.position.y}`);
            });
        }
    }, [nodes]);

    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    const updateStyle = (id, active) => {
        setNodes((objs) =>
            objs.map((obj) =>
                obj.id === id
                    ? { ...obj, data: { ...obj.data, active } }
                    : obj
            )
        );
        setEdges((objs) =>
            objs.map((obj) =>
                obj.id === id
                    ? { ...obj, data: { ...obj.data, active } }
                    : obj
            )
        );
    };

    useEffect(() => {
        if (!buttonClicked && !aiReplied) return;
        if (animationLock.current) return; // Prevent overlapping animations
        animationLock.current = true;

        const animate = async (ids, active) => {
            ids.forEach((id) => updateStyle(id, active));
            await delay(DELAY_DURATION);
        };

        const animateGraph = async () => {
            if (!aiReplied) {
                // Forward animation
                await animate([NODE_IDS.BUYER], HIGHLIGHT.ON);
                await animate([NODE_IDS.BUYER], HIGHLIGHT.OFF);
                await animate([EDGE_IDS.BUYER_TO_SLIM], HIGHLIGHT.ON);
                await animate([EDGE_IDS.BUYER_TO_SLIM], HIGHLIGHT.OFF);

                await animate([NODE_IDS.SLIM], HIGHLIGHT.ON);
                await animate([NODE_IDS.SLIM], HIGHLIGHT.OFF);
                await animate([EDGE_IDS.SLIM_TO_SOMMELIER], HIGHLIGHT.ON);
                await animate([EDGE_IDS.SLIM_TO_SOMMELIER], HIGHLIGHT.OFF);

                await animate([NODE_IDS.SOMMELIER], HIGHLIGHT.ON);
                await animate([NODE_IDS.SOMMELIER], HIGHLIGHT.OFF);
            } else {
                // Backward animation
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