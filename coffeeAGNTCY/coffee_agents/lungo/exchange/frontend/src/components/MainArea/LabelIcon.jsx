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

import React from 'react';
import googleIcon from '../../assets/google_icon.png';
import mcpIcon from '../../assets/mcp_icon.png';
import { EdgeLabelIcon } from '../../utils/const.js';

const LabelIcon = ({ type, altText = 'icon', size = 16 }) => {
    const iconPath = type === EdgeLabelIcon.GOOGLE ? googleIcon : type === EdgeLabelIcon.MCP ? mcpIcon : null;

    if (!iconPath) return null;

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '50%',
                backgroundColor: 'white',
                width: `${size}px`,
                height: `${size}px`,
            }}
        >
            <img
                src={iconPath}
                alt={altText}
                style={{ width: `${size - 4}px`, height: `${size - 4}px` }}
            />
        </div>
    );
};

export default LabelIcon;