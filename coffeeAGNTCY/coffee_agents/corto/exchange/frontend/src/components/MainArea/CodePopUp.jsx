/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React, { useState } from 'react';
import { IoCodeSlash, IoCopy } from 'react-icons/io5';
import { css } from '@emotion/react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './styles/CodePopUp.css';

const dynamicOverlayStyle = (showCode) => css`
  opacity: ${showCode ? 1 : 0};
  pointer-events: ${showCode ? 'auto' : 'none'};
  transition: opacity 0.3s ease-in-out;
`;

const CodePopUp = () => {
    const [showCode, setShowCode] = useState(false);
    const [showBadge, setShowBadge] = useState(false);

    // Toggle the visibility of the code popup
    const toggleCode = () => setShowCode(!showCode);

// Code block to display
    const codeBlock = `
# ==========================
# Server setup
# ==========================
from a2a.server import A2AServer
from agntcy_app_sdk.factory import GatewayFactory
from agntcy_app_sdk.factory import ProtocolTypes

# Initialize the server with agent card and request handler
server = A2AServer(agent_card=agent_card, request_handler=request_handler)

# Create a transport and bridge for communication
factory = GatewayFactory()
transport = factory.create_transport("SLIM", "localhost:46357")
bridge = factory.create_bridge(server, transport=transport)

# Start the bridge
await bridge.start()

# ==========================
# Client setup
# ==========================
from agntcy_app_sdk.factory import GatewayFactory
from agntcy_app_sdk.protocols.a2a.gateway import A2AProtocol

# Enable tracing and create a transport
factory = GatewayFactory(enable_tracing=True)
agp_transport = factory.create_transport("SLIM", "http://localhost:46357")

# Create a topic and client for communication
topic = A2AProtocol.create_agent_topic(a2a_agent_card)
client = await factory.create_client("A2A", agent_topic=topic, transport=agp_transport)
`;

    // Copy the code block to clipboard and show a badge
    const copyToClipboard = () => {
        navigator.clipboard.writeText(codeBlock);
        setShowBadge(true);
        setTimeout(() => setShowBadge(false), 2000); // Hide badge after 2 seconds
    };

    return (
        <>
            {/* Icon to toggle the code popup */}
            <div className="code-popup-icon-style" onClick={toggleCode}>
                <IoCodeSlash size={20} color="#187ADC" />
            </div>
            {/* Code overlay */}
            <div
                className={`code-popup-overlay-style ${showCode ? 'show' : ''}`}
                css={dynamicOverlayStyle(showCode)}
                onClick={toggleCode}
            >
                {showCode && (
                    <div
                        className="code-popup-code-style"
                        onClick={(e) => e.stopPropagation()} // Prevent toggle when clicking inside the code block
                    >
                        <div className="code-popup-header">
                            <IoCopy
                                size={20}
                                color="#187ADC"
                                className="copy-icon"
                                onClick={(e) => {
                                    e.stopPropagation(); // Prevent closing the popup
                                    copyToClipboard();
                                }}
                            />
                            {showBadge && (
                                <span className={`copy-badge ${showBadge ? 'show' : ''}`}>Copied!</span>
                            )}
                        </div>
                        <SyntaxHighlighter language="python" style={vscDarkPlus}>
                            {codeBlock.trim()}
                        </SyntaxHighlighter>
                    </div>
                )}
            </div>
        </>
    );
};

export default CodePopUp;