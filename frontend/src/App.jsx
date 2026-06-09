import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography } from '@mui/material';
import JobForm from './pages/JobForm';
import JobDashboard from './pages/JobDashboard';

function App() {
  return (
    <Router>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">
            dv2png - FISH Image Converter
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<JobForm />} />
          <Route path="/jobs" element={<JobDashboard />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
