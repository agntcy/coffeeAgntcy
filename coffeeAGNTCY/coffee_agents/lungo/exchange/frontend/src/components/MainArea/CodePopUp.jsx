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
import React, { useState } from 'react';
import { IoCodeSlash } from 'react-icons/io5';
import { css } from '@emotion/react';
import imageSrc from '../../assets/agntcy_sdk_code.png';
import './styles/CodePopUp.css';

const dynamicOverlayStyle = (showImage) => css`
  opacity: ${showImage ? 1 : 0};
  pointer-events: ${showImage ? 'auto' : 'none'};
  transition: opacity 0.3s ease-in-out;
`;

const CodePopUp = () => {
    const [showImage, setShowImage] = useState(false);

    const toggleImage = () => setShowImage(!showImage);

    return (
        <>
            {/* Icon to toggle the image */}
            <div className="code-popup-icon-style" onClick={toggleImage}>
                <IoCodeSlash size={20} color="#187ADC" />
            </div>
            {/* Image overlay */}
            <div
                className={`code-popup-overlay-style ${showImage ? 'show' : ''}`}
                css={dynamicOverlayStyle(showImage)}
                onClick={toggleImage}
            >
                {showImage && <img src={imageSrc} alt="Code Image" className="code-popup-image-style" />}
            </div>
        </>
    );
};

export default CodePopUp;