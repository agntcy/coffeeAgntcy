/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

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