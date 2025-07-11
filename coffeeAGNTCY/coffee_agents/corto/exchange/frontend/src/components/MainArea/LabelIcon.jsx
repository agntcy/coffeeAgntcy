/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React from 'react';
import { css } from '@emotion/react';
import a2aIcon from '../../assets/a2a_icon.svg';
import mcpIcon from '../../assets/mcp_icon.png';
import { EdgeLabelIcon } from '../../utils/const.js';
import './styles/LabelIcon.css';

const LabelIcon = ({ type, altText = 'icon', size = 16 }) => {
    const iconPath = type === EdgeLabelIcon.A2A ? a2aIcon : type === EdgeLabelIcon.MCP ? mcpIcon : null;

    if (!iconPath) return null;

    const isA2A = type === EdgeLabelIcon.A2A;
    const dynamicStyle = css`
        width: ${size}px;
        height: ${size}px;
    `;

    return (
        <div className="label-icon-container" css={dynamicStyle}>
            <img
                src={iconPath}
                alt={altText}
                className="label-icon-image"
                style={{ opacity: isA2A ? 0.8 : 1 }}
            />
        </div>
    );
};

export default LabelIcon;