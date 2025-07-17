import React, { useState } from 'react';
import axios from 'axios';
import { FaIdBadge } from 'react-icons/fa';

const DEFAULT_EXCHANGE_APP_API_URL = 'http://localhost:8000';

const Badge = ({ farmName }) => {
    const [toggled, setToggled] = useState(false);
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    const handleClick = async () => {
        setLoading(true);
        setErrorMessage('');

        try {
            const apiUrl = import.meta.env.VITE_EXCHANGE_APP_API_URL || DEFAULT_EXCHANGE_APP_API_URL;
            const resp = await axios.post(`${apiUrl}/farms/toggle-badge`, {
                farm_name: farmName,
            });

            console.log('Toggle badge response:', farmName, resp.data.client_id);

            // Set toggled based on client_id ending
            setToggled(resp.data.client_id.endsWith('-invalid'));
        } catch (error) {
            setErrorMessage(error.response?.data?.detail || error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <button
                onClick={handleClick}
                style={{
                    padding: '10px',
                    backgroundColor: toggled ? '#F8C7C7' : '#187ADC', // Red if toggled, blue otherwise
                    color: '#fff',
                    border: 'none',
                    borderRadius: '50%',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
                disabled={loading}
            >
                <FaIdBadge size={20} />
            </button>
            {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
        </div>
    );
};

export default Badge;