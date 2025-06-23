/** @jsxImportSource @emotion/react */
import React from 'react';
import { css } from '@emotion/react';
import { EdgeLabelRenderer } from '@xyflow/react';

const MCPOverSlimEdgeLabel = ({ x, y }) => {
    const dynamicStyle = css`
        position: absolute;
        left: ${x}px;
        top: ${y}px;
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        padding: 4px 10px;
        gap: 6px;
    `;

    return (
        <EdgeLabelRenderer>
            <div className="custom-edge-label mcp-over-slim-edge-label" css={dynamicStyle}>
                <div
                    style={{
                        fontWeight: 'bold',
                        fontSize: '12px',
                        color: '#333',
                    }}
                >
                    MCP
                </div>
                <div
                    style={{
                        fontSize: '14px',
                        color: '#666',
                    }}
                >
                    SLIM
                </div>
            </div>
        </EdgeLabelRenderer>
    );
};

export default MCPOverSlimEdgeLabel;