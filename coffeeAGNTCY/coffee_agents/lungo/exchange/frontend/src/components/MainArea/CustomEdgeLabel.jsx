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
import { EdgeLabelRenderer } from '@xyflow/react';

const CustomEdgeLabel = ({ x, y, label, icon, backgroundColor = '#F5F5F5' }) => {
    return (
        <EdgeLabelRenderer>
            <div
                style={{
                    position: 'absolute',
                    left: `${x}px`,
                    top: `${y}px`,
                    backgroundColor: `${backgroundColor}`,
                    width: '50px',
                    height: '20px',
                    color:  'black',
                    padding: '2px 5px',
                    border: `0.1px solid #FFFFFF`,
                    borderRadius: '1em',
                    fontSize: '10px',
                    fontWeight: 'thin',
                    fontFamily: "'CiscoSansTT', sans-serif",
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderLeft: '5px solid orange',

                }}
            >
                <div
                    style={{
                        position: 'absolute',
                        left: '25%',
                        transform: 'translateX(-50%)',
                    }}
                >
                    {icon}
                </div>
                <div
                    style={{
                        position: 'absolute',
                        right: '30%',
                        transform: 'translateX(50%)',
                        textAlign: 'right',
                    }}
                >
                    {label}
                </div>
            </div>
        </EdgeLabelRenderer>
    );
};

export default CustomEdgeLabel;