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
    `;

    return (
        <EdgeLabelRenderer>
            <div className="custom-edge-label mcp-over-slim-edge-label" css={dynamicStyle}>
                <div className="mcp-text">MCP</div>
                <div className="slim-text">SLIM</div>
            </div>
        </EdgeLabelRenderer>
    );
};

export default MCPOverSlimEdgeLabel;