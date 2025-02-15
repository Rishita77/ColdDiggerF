import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const History = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get('/api/application-history/');
        setApplications(response.data.history);
      } catch (err) {
        setError('Failed to load application history');
        console.error('Error fetching history:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const downloadFile = async (fileId, fileType) => {
    try {
      const response = await axios.get(`/api/download-file/${fileId}/${fileType}/`, {
        responseType: 'blob'
      });

      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Set filename based on type
      const extension = fileType === 'resume' ? '.pdf' : '.csv';
      link.setAttribute('download', `${fileType}_${fileId}${extension}`);
      
      // Append to html link element page
      document.body.appendChild(link);
      
      // Start download
      link.click();
      
      // Clean up and remove the link
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) return <div className="container">Loading...</div>;
  if (error) return <div className="container">Error: {error}</div>;

  return (
    <div className="container">
      <h2>Application History</h2>
      {applications.length === 0 ? (
        <p>No applications found.</p>
      ) : (
        <div className="history-content">
          {applications.map((item, index) => (
            <div key={item.id} className="history-item">
              <h3>Application #{applications.length - index}</h3>
              <p>Position: {item.position}</p>
              <p>Date: {formatDate(item.application_date)}</p>
              <div className="download-links">
                {item.resume && (
                  <button 
                    onClick={() => downloadFile(item.id, 'resume')}
                    className="btn" 
                    style={{ marginRight: '1rem' }}
                  >
                    Download Resume
                  </button>
                )}
                {item.contacts_csv && (
                  <button 
                    onClick={() => downloadFile(item.id, 'csv')}
                    className="btn"
                  >
                    Download CSV
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default History;