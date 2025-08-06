/**
* Copyright AGNTCY Contributors (https://github.com/agntcy)
* SPDX-License-Identifier: Apache-2.0
**/

export interface Message {
    role: 'assistant' | 'user';
    content: string;
    id: string;
    animate: boolean;
}
