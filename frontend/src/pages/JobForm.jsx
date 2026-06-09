import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Slider,
  Typography,
  Grid,
} from '@mui/material';

const steps = [
  'User Information',
  'File Paths',
  'Channel Assignment',
  'Processing Options',
  'Review & Submit',
];

function JobForm() {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [config, setConfig] = useState(null);
  const [formData, setFormData] = useState({
    your_name: '',
    imaged_by: '',
    input_directory: '',
    output_directory: '',
    channel_names: {},
    include_channels: [],
    scale_factor: 2.0,
    brightness_factor: 2,
    execution_mode: 'local',
  });

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await apiService.getConfig();
      setConfig(response.data.data);
      setFormData(prev => ({
        ...prev,
        channel_names: response.data.data.channels,
      }));
    } catch (err) {
      setError('Failed to load configuration');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleChannelToggle = (channel) => {
    setFormData(prev => ({
      ...prev,
      include_channels: prev.include_channels.includes(channel)
        ? prev.include_channels.filter(c => c !== channel)
        : [...prev.include_channels, channel],
    }));
  };

  const handleSliderChange = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const validateStep = () => {
    if (activeStep === 0) {
      if (!formData.your_name || !formData.imaged_by) {
        setError('Please fill in all user information fields');
        return false;
      }
    } else if (activeStep === 1) {
      if (!formData.input_directory || !formData.output_directory) {
        setError('Please provide both input and output directories');
        return false;
      }
    } else if (activeStep === 4) {
      if (formData.include_channels.length === 0) {
        setError('Please select at least one channel to include in composite');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep()) {
      setError('');
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep()) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiService.submitJob(formData);
      setSuccess(`Job submitted successfully! Job ID: ${response.data.data.job_id}`);
      setFormData({
        your_name: '',
        imaged_by: '',
        input_directory: '',
        output_directory: '',
        channel_names: config?.channels || {},
        include_channels: [],
        scale_factor: 2.0,
        brightness_factor: 2,
        execution_mode: 'local',
      });
      setActiveStep(0);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to submit job');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Your Name"
              name="your_name"
              value={formData.your_name}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              label="Imaged By"
              name="imaged_by"
              value={formData.imaged_by}
              onChange={handleInputChange}
              fullWidth
            />
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Input Directory"
              name="input_directory"
              value={formData.input_directory}
              onChange={handleInputChange}
              fullWidth
              placeholder="/path/to/input"
            />
            <TextField
              label="Output Directory"
              name="output_directory"
              value={formData.output_directory}
              onChange={handleInputChange}
              fullWidth
              placeholder="/path/to/output"
            />
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography>Configure channel names (if different from defaults)</Typography>
            {config?.channels && Object.entries(config.channels).map(([idx, name]) => (
              <TextField
                key={idx}
                label={`Channel ${idx}`}
                value={formData.channel_names[idx] || name}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  channel_names: { ...prev.channel_names, [idx]: e.target.value }
                }))}
                fullWidth
              />
            ))}
          </Box>
        );

      case 3:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="subtitle1">Select channels for composite image:</Typography>
              <FormGroup>
                {config?.channels && Object.values(config.channels).map((channel) => (
                  <FormControlLabel
                    key={channel}
                    control={
                      <Checkbox
                        checked={formData.include_channels.includes(channel)}
                        onChange={() => handleChannelToggle(channel)}
                      />
                    }
                    label={channel}
                  />
                ))}
              </FormGroup>
            </Box>

            <Box>
              <Typography variant="subtitle1">Scale Factor: {formData.scale_factor}</Typography>
              <Slider
                value={formData.scale_factor}
                onChange={(e, value) => handleSliderChange('scale_factor', value)}
                min={0.5}
                max={5}
                step={0.1}
              />
            </Box>

            <Box>
              <Typography variant="subtitle1">Brightness Factor: {formData.brightness_factor}</Typography>
              <Slider
                value={formData.brightness_factor}
                onChange={(e, value) => handleSliderChange('brightness_factor', value)}
                min={1}
                max={5}
                step={1}
              />
            </Box>
          </Box>
        );

      case 4:
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Review Your Settings</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2">Your Name:</Typography>
                  <Typography>{formData.your_name}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Imaged By:</Typography>
                  <Typography>{formData.imaged_by}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Input Directory:</Typography>
                  <Typography>{formData.input_directory}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Output Directory:</Typography>
                  <Typography>{formData.output_directory}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Channels in Composite:</Typography>
                  <Typography>{formData.include_channels.join(', ')}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Scale Factor:</Typography>
                  <Typography>{formData.scale_factor}</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  if (!config) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ py: 4 }}>
      <Stepper activeStep={activeStep}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}

      <Box sx={{ mt: 4 }}>
        {renderStepContent()}
      </Box>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
        <Button disabled={activeStep === 0} onClick={handleBack}>
          Back
        </Button>
        <Box>
          {activeStep === steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Submit Job'}
            </Button>
          ) : (
            <Button variant="contained" onClick={handleNext}>
              Next
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default JobForm;
