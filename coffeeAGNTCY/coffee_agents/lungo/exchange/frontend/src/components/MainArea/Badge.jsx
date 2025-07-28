import React from 'react';
import { FarmName } from '../../utils/const.js'; // Adjust the import path as necessary

const Badge = ({ farmName }) => {
    const isValid = farmName !== FarmName.BrazilCoffeeFarm; // Example condition for validity

    return (
        <div>
            <button
                style={{
                    padding: '4px 4px',
                    backgroundColor: isValid ? '#00935D' : '#C0244C', // Green for valid, red for not valid
                    color: '#fff',
                    border: 'none',
                    borderRadius: '3px', // Rounded rectangle
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    letterSpacing: '0.5px', // Adjust font spacing here
                }}
            >
                {isValid ? 'Validated' : 'Not Validated'}
            </button>
        </div>
    );
};

export default Badge;