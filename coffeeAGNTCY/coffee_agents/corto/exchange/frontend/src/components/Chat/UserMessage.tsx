/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

import React from 'react';
import { User } from 'lucide-react';

interface UserMessageProps {
    content: string;
}

const UserMessage: React.FC<UserMessageProps> = ({ content }) => {
    return (
        <div className="flex flex-row items-start gap-1 w-[880px] h-10">
           
            <div className="flex justify-center items-center w-10 h-10 bg-[#00142B] rounded-full">
                <User size={20} className="text-white" />
            </div>
            
        
            <div className="flex flex-col justify-center items-start p-1 px-2 w-[814px] h-10 rounded">
                <div className="w-[814px] h-10 p-1 px-2 rounded flex items-center">
                    <div className="font-inter font-normal text-sm leading-5 text-white">
                        {content}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserMessage;
