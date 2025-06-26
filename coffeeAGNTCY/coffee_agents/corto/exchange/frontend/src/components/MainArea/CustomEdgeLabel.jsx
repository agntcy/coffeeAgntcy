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
import { EdgeLabelRenderer } from '@xyflow/react';
import { css } from '@emotion/react';
import './styles/CustomEdgeLabel.css';

const CustomEdgeLabel = ({ x, y, label, icon }) => {
    const dynamicStyle = css`
        position: absolute;
        left: ${x}px;
        top: ${y}px;
    `;

    const getLabelClasses = (label) => {
        const baseClass = 'custom-edge-label';
        const iconClass = 'custom-edge-label-icon';
        const textClass = 'custom-edge-label-text';

        if (label?.toLowerCase().endsWith('slim')) {
            return {
                labelClass: `${baseClass} ${baseClass}-with-slim`,
                iconClass: `${iconClass} ${iconClass}-with-slim`,
                textClass: `${textClass} ${textClass}-with-slim`,
            };
        }

        return { labelClass: baseClass, iconClass, textClass };
    };

    const { labelClass, iconClass, textClass } = getLabelClasses(label);

    return (
        <EdgeLabelRenderer>
            <div className={labelClass} css={dynamicStyle}>
                <div className={iconClass}>{icon}</div>
                <div className={textClass}>{label}</div>
            </div>
        </EdgeLabelRenderer>
    );
};

export default CustomEdgeLabel;