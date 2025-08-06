/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React, { useEffect, useRef } from 'react';
import {
    ReactFlow,
    ReactFlowProvider,
    useNodesState,
    useEdgesState,
    useReactFlow,
    Controls,
    Node,
    Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './ReactFlow.css';
import SlimNode from './Graph/SlimNode';
import CustomEdge from './Graph/CustomEdge';
import CustomNode from './Graph/CustomNode';
import { graphConfig } from '@/utils/graphConfigs';

const proOptions = { hideAttribution: true };

const nodeTypes = {
    slimNode: SlimNode,
    customNode: CustomNode,
};

const edgeTypes = {
    custom: CustomEdge,
};


interface AnimationStep {
    ids: string[];
}

interface GraphConfig {
    nodes: Node[];
    edges: Edge[];
    animationSequence: AnimationStep[];
}

interface MainAreaProps {
    buttonClicked: boolean;
    setButtonClicked: (clicked: boolean) => void;
    aiReplied: boolean;
    setAiReplied: (replied: boolean) => void;
}

const DELAY_DURATION = 500; 
const HIGHLIGHT = {
    ON: true,
    OFF: false,
} as const;

const MainArea: React.FC<MainAreaProps> = ({ 
    buttonClicked, 
    setButtonClicked, 
    aiReplied, 
    setAiReplied 
}) => {
   
    const config: GraphConfig = graphConfig;
    const { fitView } = useReactFlow();
    
    const [nodes, setNodes, onNodesChange] = useNodesState(config.nodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(config.edges);
    const animationLock = useRef<boolean>(false); 

    useEffect(() => {
        const newConfig: GraphConfig = graphConfig;
        setNodes(newConfig.nodes);
        setEdges(newConfig.edges);
        
        setTimeout(() => {
            fitView({ 
                padding: 0.3, 
                duration: 300, 
                maxZoom: 0.8 
            });
        }, 100); 
    }, [setNodes, setEdges, fitView]);

    const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

    const updateStyle = (id: string, active: boolean): void => {
        setNodes((objs: Node[]) =>
            objs.map((obj: Node) =>
                obj.id === id
                    ? { ...obj, data: { ...obj.data, active } }
                    : obj
            )
        );
        setEdges((objs: Edge[]) =>
            objs.map((obj: Edge) =>
                obj.id === id
                    ? { ...obj, data: { ...obj.data, active } }
                    : obj
            )
        );
    };

    useEffect(() => {
        if (!buttonClicked && !aiReplied) return;
        
        const waitForAnimationAndRun = async () => {
            while (animationLock.current) {
                await delay(100);
            }
            
            animationLock.current = true;

            const animate = async (ids: string[], active: boolean): Promise<void> => {
                ids.forEach((id: string) => updateStyle(id, active));
                await delay(DELAY_DURATION);
            };

            const animateGraph = async (): Promise<void> => {
                if (!aiReplied) {
                    const animationSequence: AnimationStep[] = config.animationSequence;
                    for (const step of animationSequence) {
                        await animate(step.ids, HIGHLIGHT.ON);
                        await animate(step.ids, HIGHLIGHT.OFF);
                    }
                } else {
                    setAiReplied(false);
                }

                setButtonClicked(false);
                animationLock.current = false; 
            };

            await animateGraph();
        };

        waitForAnimationAndRun();
    }, [buttonClicked, setButtonClicked, aiReplied, setAiReplied, config.animationSequence]);

    return (
        <div className="flex flex-col items-start p-0 w-full h-full bg-[#0E1116] flex-none order-1 self-stretch flex-grow">
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

const MainAreaWithProvider: React.FC<MainAreaProps> = (props) => (
    <ReactFlowProvider>
        <MainArea {...props} />
    </ReactFlowProvider>
);

export default MainAreaWithProvider;
