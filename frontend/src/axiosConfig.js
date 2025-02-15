// In your React app where you configure axios

import axios from 'axios';

// Configure axios defaults
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

// Update your API calls to include credentials
const sendEmail = async (contactId) => {
    try {
        const response = await axios.post('/api/send-email/', {
            contactId: contactId
        }, {
            withCredentials: true
        });
        return response.data;
    } catch (error) {
        console.error('Error sending email:', error);
        throw error;
    }
};