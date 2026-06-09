import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

function JobDashboard() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await apiService.listJobs(50);
      setJobs(response.data.data.jobs);
      setLoading(false);
    } catch (err) {
      setError('Failed to load jobs');
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'processing':
        return 'info';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleCancelJob = async (jobId) => {
    try {
      await apiService.cancelJob(jobId);
      fetchJobs();
    } catch (err) {
      setError('Failed to cancel job');
    }
  };

  const handleDownloadResults = async (jobId) => {
    try {
      const results = await apiService.getJobResults(jobId);
      const files = results.data.data.files;
      
      if (files.length === 0) {
        setError('No result files available');
        return;
      }

      // Download each file
      for (const file of files) {
        if (file.name.endsWith('.pdf') || file.name.endsWith('.png')) {
          const blob = await apiService.downloadFile(jobId, file.path);
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = file.name;
          document.body.appendChild(link);
          link.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(link);
        }
      }
    } catch (err) {
      setError('Failed to download results');
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h5" gutterBottom>
        Job Dashboard
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {jobs.length === 0 ? (
        <Alert severity="info">
          No jobs yet. <Button onClick={() => navigate('/')}>Create a new job</Button>
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Job ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Input</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.job_id}>
                  <TableCell>{job.job_id.substring(0, 8)}...</TableCell>
                  <TableCell>
                    <Chip
                      label={job.status}
                      color={getStatusColor(job.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{new Date(job.created_at).toLocaleString()}</TableCell>
                  <TableCell>{job.parameters.input_directory}</TableCell>
                  <TableCell>
                    {job.status === 'processing' && (
                      <>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        <Button
                          size="small"
                          onClick={() => handleCancelJob(job.job_id)}
                        >
                          Cancel
                        </Button>
                      </>
                    )}
                    {job.status === 'completed' && (
                      <Button
                        size="small"
                        onClick={() => handleDownloadResults(job.job_id)}
                      >
                        Download
                      </Button>
                    )}
                    {job.status === 'failed' && (
                      <Typography color="error" variant="caption">
                        {job.error_message}
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Button
        variant="contained"
        onClick={() => navigate('/')}
        sx={{ mt: 2 }}
      >
        New Job
      </Button>
    </Box>
  );
}

export default JobDashboard;
