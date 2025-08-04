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
import { PatternType } from '@/App';

interface CodePopUpProps {
    showCode: boolean;
    selectedPattern: PatternType;
    onClose: () => void;
}

const dynamicOverlayStyle = (showCode: boolean) => css`
  opacity: ${showCode ? 1 : 0};
  pointer-events: ${showCode ? 'auto' : 'none'};
  transition: opacity 0.3s ease-in-out;
`;

const CodePopUp: React.FC<CodePopUpProps> = ({ showCode, selectedPattern, onClose }) => {
    const [showBadge, setShowBadge] = useState<boolean>(false);

    const getCodeContent = (pattern: PatternType): string => {
        switch (pattern) {
            case 'slim_a2a':
                return `
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
            case 'slim_multi_a2a':
                return `
# ==========================
# SLIM Multi A2A - Lungo Demo
# ==========================
from a2a.server import A2AServer
from agntcy_app_sdk.factory import GatewayFactory

# Initialize multiple farm servers
brazil_server = A2AServer(agent_card=brazil_card, request_handler=brazil_handler)
colombia_server = A2AServer(agent_card=colombia_card, request_handler=colombia_handler) 
vietnam_server = A2AServer(agent_card=vietnam_card, request_handler=vietnam_handler)

# Create supervisor exchange
exchange_server = A2AServer(agent_card=exchange_card, request_handler=exchange_handler)

# Setup SLIM PubSub for multi-agent communication
factory = GatewayFactory()
slim_transport = factory.create_transport("SLIM", "localhost:46357")

# Start all farm bridges
for server in [brazil_server, colombia_server, vietnam_server]:
    bridge = factory.create_bridge(server, transport=slim_transport)
    await bridge.start()

# ==========================
# MCP Weather Service Integration
# ==========================
from mcp_servers.weather_service import WeatherMCPServer

# Colombia farm integrates with weather service
weather_server = WeatherMCPServer()
await weather_server.start()
`;
            case 'identity':
                return `
# ==========================
# Identity Services Demo
# ==========================
from agntcy_app_sdk.identity import IdentityProvider
from agntcy_app_sdk.factory import GatewayFactory

# Initialize identity provider
identity_provider = IdentityProvider(
    auth_service="oauth2",
    token_endpoint="https://auth.agntcy.com/token",
    userinfo_endpoint="https://auth.agntcy.com/userinfo"
)

# Setup authenticated client
factory = GatewayFactory(identity_provider=identity_provider)
authenticated_client = await factory.create_authenticated_client()

# ==========================
# Secure Agent Communication
# ==========================
from agntcy_app_sdk.protocols.identity import SecureProtocol

# Create secure communication channel
secure_channel = SecureProtocol.create_channel(
    client_id="agent_client",
    scopes=["agent:read", "agent:write"]
)

# Authenticate and establish connection
await secure_channel.authenticate()
response = await secure_channel.send_secure_message(message)
`;
            default:
                return `
# ==========================
# Select a pattern to view code
# ==========================
# Choose from:
# - SLIM A2A: Simple agent-to-agent communication
# - SLIM Multi A2A: Multi-agent supervisor pattern
# - Identity: Secure identity services
`;
        }
    };

    const codeBlock: string = getCodeContent(selectedPattern);

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