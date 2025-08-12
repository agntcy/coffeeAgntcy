/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';

const PatternEmptyState: React.FC = () => {
    return (
        <div className="flex w-full h-full bg-primary-bg justify-center items-center relative">
            <div className="flex w-[328px] flex-col items-center gap-2">
                <div className="flex flex-col items-center gap-6">
                    <div className="flex justify-center items-center w-[120px] h-[212px]">
                        <img 
                            src="/blank_pattern.svg" 
                            alt="Pattern Icon" 
                            width="120" 
                            height="212"
                        />
                    </div>

                 
                    <div className="flex flex-col items-center gap-2">
                        <div className="flex flex-col items-center gap-[10px]">
                            <span className="
                                w-[244px] h-6 text-[#FBFCFE] text-center font-[Inter] 
                                text-base font-normal leading-6 tracking-[0.5px]
                            ">
                                Select a pattern to get started
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PatternEmptyState;
