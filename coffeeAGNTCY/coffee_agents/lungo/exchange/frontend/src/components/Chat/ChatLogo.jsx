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
import React from "react";
import { css } from "@emotion/react";
import logoSrc from "../../assets/coffee_agntcy.png";

const containerStyle = css`
  height: 10%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #ddd;
  background-color: #ffffff;
  padding: 0;
`;

const imageStyle = css`
  max-height: 60%;
  max-width: 80%;
  object-fit: contain;
`;

const ChatLogo = () => {
    return (
        <div css={containerStyle}>
            <img src={logoSrc} alt="Agency Coffee Logo" css={imageStyle} />
        </div>
    );
};

export default ChatLogo;