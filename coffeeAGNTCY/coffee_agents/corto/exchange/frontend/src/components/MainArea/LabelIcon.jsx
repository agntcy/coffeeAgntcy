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