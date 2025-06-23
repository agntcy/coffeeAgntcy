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
const DELAY_DURATION = 500; // Animation delay in milliseconds

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
    BRAZIL: '3',
    COLOMBIA: '4',
    COFFEE_FARM_SITE: '5',
    VIETNAM: '6',
};

const EDGE_IDS = {
    BUYER_TO_SLIM: '1-2',
    SLIM_TO_BRAZIL: '2-3',
    SLIM_TO_COLOMBIA: '2-4',
    COLOMBIA_TO_COFFEE_FARM_SITE: '4-5',
    SLIM_TO_VIETNAM: '2-6',
};

// Initial nodes
const commonNodeData = {
    backgroundColor: COLORS.NODE.ORIGINAL.BACKGROUND,
};

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
        position: { x: 527.1332569384248, y: 76.4805787605829 },
    },
    {
        id: NODE_IDS.SLIM,
        type: 'slimNode',
        data: {
            ...commonNodeData,
            label: 'Pub/Sub (SLIM)',
        },
        position: { x: 229.02370449534635, y: 284.688426426175 },
    },
    {
        id: NODE_IDS.BRAZIL,
        type: 'customNode',
        data: {
            ...commonNodeData,
            icon: <FaWarehouse />,
            label1: 'Coffee Farm Agent',
            label2: 'Brazil',
            handles: 'target',
        },
        position: { x: 232.0903941835277, y: 503.93174725714437 },
    },
    {
        id: NODE_IDS.COLOMBIA,
        type: 'customNode',
        data: {
            ...commonNodeData,
            icon: <FaWarehouse />,
            label1: 'Coffee Farm Agent',
            label2: 'Colombia',
            handles: 'all',
        },
        position: { x: 521.266082170288, y: 505.38817113883306 },
    },
    {
        id: NODE_IDS.VIETNAM,
        type: 'customNode',
        data: {
            ...commonNodeData,
            icon: <FaWarehouse />,
            label1: 'Coffee Farm Agent',
            label2: 'Vietnam',
            handles: 'target',
        },
        position: { x: 832.9824511707582, y: 505.08339631990395 },
    },
    {
        id: NODE_IDS.COFFEE_FARM_SITE,
        type: 'customNode',
        data: {
            ...commonNodeData,
            icon: <FaCloudSun />,
            label1: 'MCP Server',
            label2: 'Weather',
            handles: 'target',
        },
        position: { x: 569.3959708104304, y: 731.9104402412228 },
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
        id: EDGE_IDS.SLIM_TO_BRAZIL,
        source: NODE_IDS.SLIM,
        target: NODE_IDS.BRAZIL,
        sourceHandle: 'bottom_left',
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
    {
        id: EDGE_IDS.COLOMBIA_TO_COFFEE_FARM_SITE,
        source: NODE_IDS.COLOMBIA,
        target: NODE_IDS.COFFEE_FARM_SITE,
        data: { label: 'mcp/slim', labelIconType: EdgeLabelIcon.MCP },
        type: 'custom',
    },
    {
        id: EDGE_IDS.SLIM_TO_VIETNAM,
        source: NODE_IDS.SLIM,
        target: NODE_IDS.VIETNAM,
        sourceHandle: 'bottom_right',
        data: { label: 'A2A', labelIconType: EdgeLabelIcon.A2A },
        type: 'custom',
    },
];

const Graph = ({ buttonClicked, setButtonClicked, aiReplied, setAiReplied }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const animationLock = useRef(false); // Lock to prevent overlapping animations

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
                await animate([EDGE_IDS.SLIM_TO_BRAZIL, EDGE_IDS.SLIM_TO_COLOMBIA, EDGE_IDS.SLIM_TO_VIETNAM], HIGHLIGHT.ON);
                await animate([EDGE_IDS.SLIM_TO_BRAZIL, EDGE_IDS.SLIM_TO_COLOMBIA, EDGE_IDS.SLIM_TO_VIETNAM], HIGHLIGHT.OFF);

                await animate([NODE_IDS.BRAZIL, NODE_IDS.COLOMBIA, NODE_IDS.VIETNAM], HIGHLIGHT.ON);
                await animate([NODE_IDS.BRAZIL, NODE_IDS.COLOMBIA, NODE_IDS.VIETNAM], HIGHLIGHT.OFF);

                await animate([EDGE_IDS.COLOMBIA_TO_COFFEE_FARM_SITE], HIGHLIGHT.ON);
                await animate([EDGE_IDS.COLOMBIA_TO_COFFEE_FARM_SITE], HIGHLIGHT.OFF);

                await animate([NODE_IDS.COFFEE_FARM_SITE], HIGHLIGHT.ON);
                await animate([NODE_IDS.COFFEE_FARM_SITE], HIGHLIGHT.OFF);
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