/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from "react";
import logoSrc from "../../assets/coffee_agntcy.png";

const ChatLogo = () => {
    return (
        <div className="chat-logo-container">
            <img src={logoSrc} alt="Agency Coffee Logo" className="chat-logo-image" />
        </div>
    );
};

export default ChatLogo;