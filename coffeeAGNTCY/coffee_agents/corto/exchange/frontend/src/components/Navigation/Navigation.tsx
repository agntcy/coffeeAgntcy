/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';
import coffeeAgntcyLogo from '@/assets/coffeeAGNTCY_logo.svg';

const Navigation: React.FC = () => {
    return (
        <div className="
            box-border flex flex-col items-start p-0 w-full h-[52px] 
            bg-[#F5F8FD] border-r border-[#DBE0E5] 
            flex-none order-0 self-stretch flex-grow-0
        ">
         
            <div className="
                box-border flex flex-row justify-between items-center 
                py-[10px] px-2 sm:px-4 gap-2 w-full h-[52px] 
                bg-[#EFF3FC] border-b border-[#D5DFF7] 
                flex-none order-0 self-stretch flex-grow-0
            ">
                <div className="
                    flex flex-row items-center p-0 gap-2 ml-2 sm:ml-4 
                    w-32 sm:w-40 h-[45px] flex-none order-0 flex-grow-0 opacity-100
                ">
                    <div className="
                        flex flex-row items-center p-0 gap-1 
                        w-32 sm:w-40 h-[45px] flex-none order-0 flex-grow-0 opacity-100
                    ">
                        <div className="
                            flex justify-center items-center gap-0.5 
                            w-auto h-[42px] flex-none order-0 flex-grow-0 opacity-100
                        ">
                            <img 
                                src={coffeeAgntcyLogo} 
                                alt="Coffee AGNTCY Logo" 
                                className="w-32 sm:w-40 h-full object-contain" 
                            />
                        </div>
                    </div>
                </div>

                <div className="
                    flex flex-row justify-end items-center p-0 gap-2 
                    flex-none order-3 flex-grow-0
                ">
                    <span className="
                        font-inter font-normal text-xs sm:text-sm leading-5 text-right
                        text-[#1D69CC] flex-none order-0 flex-grow-1
                    " style={{ letterSpacing: '0.25px' }}>
                        Version 0.4
                    </span>
                </div>
            </div>
        </div>
    );
};

export default Navigation;
