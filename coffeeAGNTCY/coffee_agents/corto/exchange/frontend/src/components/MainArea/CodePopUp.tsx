/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

/** @jsxImportSource @emotion/react */
import React, { useState } from 'react';
import { IoCopy } from 'react-icons/io5';
import { css } from '@emotion/react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodePopUpProps {
    showCode: boolean;
    onClose: () => void;
}

const dynamicOverlayStyle = (showCode: boolean) => css`
  opacity: ${showCode ? 1 : 0};
  pointer-events: ${showCode ? 'auto' : 'none'};
  transition: opacity 0.3s ease-in-out;
`;

const CodePopUp: React.FC<CodePopUpProps> = ({ showCode, onClose }) => {
    const [showBadge, setShowBadge] = useState<boolean>(false);

    // SLIM A2A code content
    const codeBlock = `
# ==========================
# SLIM A2A - Corto Demo
# ==========================
from a2a.server import A2AServer
from agntcy_app_sdk.factory import GatewayFactory

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

    const copyToClipboard = (): void => {
        navigator.clipboard.writeText(codeBlock);
        setShowBadge(true);
        setTimeout(() => setShowBadge(false), 2000); 
    };

    return (
        <div
            className={`fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 flex items-center justify-center pt-8 pb-12 z-20 transition-opacity duration-300 ease-in-out ${showCode ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
            css={dynamicOverlayStyle(showCode)}
            onClick={onClose}
        >
            {showCode && (
                <div
                    className="max-w-[90%] max-h-[80%] overflow-auto bg-black text-[#333] p-[15px] rounded-lg font-[Courier_New,Courier,monospace] text-sm shadow-[0_2px_4px_rgba(0,0,0,0.2)] whitespace-pre-wrap break-words animate-scaleIn"
                    onClick={(e) => e.stopPropagation()} 
                >
                    <div className="flex justify-end mt-[10px] mb-[10px]">
                        <IoCopy
                            size={20}
                            color="#187ADC"
                            className="cursor-pointer mr-[10px]"
                            onClick={(e) => {
                                e.stopPropagation(); 
                                copyToClipboard();
                            }}
                        />
                        {showBadge && (
                            <span className={`bg-[rgba(24,122,220,0.7)] text-white py-[5px] px-[10px] rounded-xl text-[9px] transition-all duration-500 ease-in-out ${showBadge ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`}>
                                Copied!
                            </span>
                        )}
                    </div>
                    <SyntaxHighlighter language="python" style={vscDarkPlus}>
                        {codeBlock.trim()}
                    </SyntaxHighlighter>
                </div>
            )}
        </div>
    );
};

export default CodePopUp;