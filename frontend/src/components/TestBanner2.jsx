import React from 'react';

const TestBanner2 = () => {
  return (
    <div className="test-banner" style={{
      backgroundColor: '#fff9c4',
      padding: '15px',
      borderRadius: '5px',
      marginBottom: '20px',
      border: '2px solid #fbc02d',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ color: '#a65e1b', marginBottom: '10px', fontWeight: '600' }}>Test Account Credentials (Google)</h3>
      <p style={{ marginBottom: '5px', color: '#333' }}>Please select 'Use another account' if/when prompted by Google for OAuth after clicking the below button, and enter the following credentials to log in:</p>
      <div style={{ 
        backgroundColor: '#fff',
        padding: '12px',
        borderRadius: '4px',
        border: '1px solid #fff176'
      }}>
        <p style={{ marginBottom: '8px', color: '#000' }}><strong>Email:</strong> colddigger14@gmail.com</p>
        <p style={{ color: '#000' }}><strong>Password:</strong> WeWillWin</p>
      </div>
      <p style={{ marginBottom: '5px', color: '#333' }}>Once logged in, click the button below again.</p>
    </div>
  );
};

export default TestBanner2;