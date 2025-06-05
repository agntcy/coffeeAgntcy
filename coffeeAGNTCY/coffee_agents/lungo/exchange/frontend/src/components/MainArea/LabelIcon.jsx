import React from 'react';
import a2aIcon from '../../assets/a2a_icon.png';
import mcpIcon from '../../assets/mcp_icon.png';
import { EdgeLabelIcon } from '../../utils/const.js';

const LabelIcon = ({ type, altText = 'icon', size = 16 }) => {
    const iconPath = type === EdgeLabelIcon.A2A ? a2aIcon : type === EdgeLabelIcon.MCP ? mcpIcon : null;

    if (!iconPath) return null;

    const isA2A = type === EdgeLabelIcon.A2A;
    const parentWidth = isA2A ? size + 11 : size;
    const parentHeight = isA2A ? size - 2 : size;
    const borderRadius = isA2A ? '25%' : '50%';

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: borderRadius,
                backgroundColor: 'white',
                width: `${parentWidth}px`,
                height: `${parentHeight}px`,
                overflow: 'hidden', // Ensures the image stays within the circle
            }}
        >
            <img
                src={iconPath}
                alt={altText}
                style={{
                    width: '100%',
                    height: '100%',
                    opacity: type === EdgeLabelIcon.A2A ? 0.8 : 1, // Make lighter if A2A
                }}
            />
        </div>
    );
};

export default LabelIcon;