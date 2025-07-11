/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { css } from '@emotion/react';
import a2aIcon from '../../assets/a2a_icon.png';
import { EdgeLabelRenderer } from '@xyflow/react';

const A2AEdgeLabel = ({ x, y}) => {
    const dynamicStyle = css`
        position: absolute;
        left: ${x}px;
        top: ${y}px;
    `;

    return (
        <EdgeLabelRenderer>
            <div className={`custom-edge-label`} css={dynamicStyle} style={{ display: 'flex', alignItems: 'center' }}>
                <img
                    src={a2aIcon}
                    alt="A2A Icon"
                    style={{
                        width: '65%',
                        height: '65%',
                        opacity: 0.9, // Slightly lighter for A2A
                        borderRadius: '0.5em', // Rounded corners for A2A
                    }}
                />
                <span style={{ marginLeft: '4px', fontSize: '14px', fontWeight: 'thin', color: '#000' }}>SLIM</span>
            </div>
        </EdgeLabelRenderer>
    );
};

export default A2AEdgeLabel;