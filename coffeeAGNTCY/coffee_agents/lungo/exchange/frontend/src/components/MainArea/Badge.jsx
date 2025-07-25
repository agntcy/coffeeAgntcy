/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import React from 'react';
import { FaIdBadge } from 'react-icons/fa';
import { FarmName } from '../../utils/const.js'; // Adjust the import path as necessary

const Badge = ({ farmName }) => {
    return (
        <div>
            <button
                style={{
                    padding: '10px',
                    // Brazil Coffee Farm doesn't have valid badge, so we use a different color
                    backgroundColor: farmName ===  FarmName.BrazilCoffeeFarm ? '#E63939' : '#187ADC',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <FaIdBadge size={20} />
            </button>
        </div>
    );
};

export default Badge;
