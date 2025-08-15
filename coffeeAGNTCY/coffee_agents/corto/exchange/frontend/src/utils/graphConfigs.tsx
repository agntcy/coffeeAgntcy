/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */

import { PiCoffeeBeanThin } from "react-icons/pi";
import supervisorIcon from '@/assets/supervisor.svg';

interface GraphConfig {
    title: string;
    nodes: any[];
    edges: any[];
    animationSequence: { ids: string[] }[];
}

const CoffeeBeanIcon = <PiCoffeeBeanThin style={{ transform: 'rotate(-30deg)', fontSize: '1.65em' }} />;

const commonNodeData = {
    backgroundColor: '#F5F5F5',
};


const SLIM_A2A_CONFIG: GraphConfig = {
    title: 'SLIM A2A Coffee Agent Communication',
    nodes: [
        {
            id: '1',
            type: 'customNode',
            data: {
                ...commonNodeData,
                icon: <img 
                    src={supervisorIcon} 
                    alt="Supervisor Icon" 
                    style={{ 
                        marginLeft: '2.5px', 
                        width: '24px', 
                        height: '24px',
                        filter: 'brightness(0) invert(1)', 
                        objectFit: 'contain'
                    }} 
                />,
                label1: 'Supervisor Agent',
                label2: 'Buyer',
                handles: 'source',
                githubLink: 'https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/corto/exchange',
            },
            position: { x: 529.1332569384248, y: 159.4805787605829 },
        },
        {
            id: '2',
            type: 'customNode',
            data: {
                ...commonNodeData,
                icon: CoffeeBeanIcon,
                label1: 'Q Grader Agent',
                label2: 'Sommelier',
                handles: 'target',
                githubLink: 'https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/corto/farm',
            },
            position: { x: 534.0903941835277, y: 582.9317472571444 },
        },
    ],
    edges: [
        {
            id: '1-2',
            source: '1',
            target: '2',
            data: { label: 'A2A' },
            type: 'custom',
        },
    ],
    animationSequence: [
        { ids: ['1'] },
        { ids: ['1-2'] },
        { ids: ['2'] },
    ]
};

export const graphConfig = SLIM_A2A_CONFIG;
