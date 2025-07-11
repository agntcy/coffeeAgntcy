/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { css } from '@emotion/react';
import './styles/CustomNode.css';
import {DefaultHandleColor} from "./CustomNode.jsx";

const SlimNode = ({ data }) => {
    const nodeClass = `node slim-node ${data.active ? 'node-active' : ''}`;

    return (
        <div className={nodeClass}>
            <div>{data.label}</div>
            <Handle
                type="target"
                id="top"
                position={Position.Top}
                style={{ width: '0.1px', height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_left"
                style={{ left: '18%', width: '0.1px', height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_center"
                style={{ left: '50%', width: '0.1px', height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="bottom_right"
                style={{ left: '82%', width: '0.1px', height: '0.1px',
                    border: `1px solid darkgrey`,
                    background: data.handleColor || DefaultHandleColor }}
            />
        </div>
    );
};

export default SlimNode;