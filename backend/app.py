"""
Flask API server for dv2png
"""

import os
import subprocess
import threading
import logging
from pathlib import Path
from typing import Dict, Tuple

from flask import Flask, request, jsonify, send_file, send_from_directory, render_template_string
from flask_cors import CORS

from processor import ImageProcessor
from models import JobMetadata, JobParameters, JobStatus, ExecutionMode, APIResponse
from job_manager import JobManager
from config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with static folder
app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# Configuration
JOBS_DIR = os.getenv('JOBS_DIR', './jobs')
CONFIG_FILE = os.getenv('CONFIG_FILE', './config.yaml')

# Initialize managers
job_manager = JobManager(JOBS_DIR)
config = get_config(CONFIG_FILE)


# ============================================================================
# Helper Functions
# ============================================================================

def execute_local_job(job: JobMetadata):
    """Execute job locally in background thread"""
    try:
        job_manager.update_job_status(job.job_id, JobStatus.PROCESSING)
        
        # Create processor
        processor = ImageProcessor(job.parameters.to_dict())
        
        # Validate config
        is_valid, error_msg = processor.validate_config()
        if not is_valid:
            job_manager.update_job_status(job.job_id, JobStatus.FAILED, error_msg)
            return
        
        # Run pipeline
        success, message = processor.run_full_pipeline()
        
        if success:
            # Save result files
            output_path = Path(processor.output_directory)
            job.output_path = str(output_path)
            job.result_files = [str(f) for f in output_path.glob('**/*') if f.is_file()]
            job_manager.update_job_status(job.job_id, JobStatus.COMPLETED)
            logger.info(f"Job {job.job_id} completed successfully")
        else:
            job_manager.update_job_status(job.job_id, JobStatus.FAILED, message)
            logger.error(f"Job {job.job_id} failed: {message}")
    
    except Exception as e:
        logger.error(f"Error executing job {job.job_id}: {e}")
        job_manager.update_job_status(job.job_id, JobStatus.FAILED, str(e))


# ============================================================================
# Web UI Endpoint
# ============================================================================

@app.route('/')
def index():
    """Serve the web UI"""
    static_file = Path(__file__).parent / 'static' / 'index.html'
    if static_file.exists():
        with open(static_file, 'r') as f:
            return f.read()
    return "Web UI not found. Run from backend directory.", 404

# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'dv2png API is running'
    }), 200


@app.route('/api/config', methods=['GET'])
def get_configuration():
    """Get default configuration and channel options"""
    try:
        config_data = config.to_dict()
        response = APIResponse(
            success=True,
            message="Configuration retrieved",
            data={
                'channels': config_data.get('channels', {}),
                'processing': config_data.get('processing', {}),
                'nas': {k: v for k, v in config_data.get('nas', {}).items() if k != 'nas_password'}
            }
        )
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        response = APIResponse(success=False, message="Error retrieving config", error=str(e))
        return jsonify(response.to_dict()), 500


@app.route('/api/jobs', methods=['POST'])
def submit_job():
    """Submit a new processing job"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['your_name', 'imaged_by', 'input_directory', 
                          'output_directory', 'include_channels']
        for field in required_fields:
            if field not in data:
                response = APIResponse(success=False, message=f"Missing required field: {field}")
                return jsonify(response.to_dict()), 400
        
        # Get channel names from config or request
        channel_names = data.get('channel_names', config.get_channels())
        
        # Create job parameters
        params = JobParameters(
            your_name=data['your_name'],
            imaged_by=data['imaged_by'],
            input_directory=data['input_directory'],
            output_directory=data['output_directory'],
            channel_names=channel_names,
            include_channels=data['include_channels'],
            scale_factor=data.get('scale_factor', 2.0),
            brightness_factor=data.get('brightness_factor', 2),
            nas_host=data.get('nas_host'),
            nas_user=data.get('nas_user'),
            nas_password=data.get('nas_password'),
            nas_share=data.get('nas_share'),
        )
        
        # Determine execution mode
        execution_mode = ExecutionMode(data.get('execution_mode', 'local'))
        
        # Create job metadata
        job = JobMetadata(
            status=JobStatus.PENDING,
            execution_mode=execution_mode,
            parameters=params
        )
        
        # Save job
        if not job_manager.save_job(job):
            response = APIResponse(success=False, message="Failed to save job")
            return jsonify(response.to_dict()), 500
        
        # Execute based on mode
        if execution_mode == ExecutionMode.LOCAL:
            # Run in background thread
            thread = threading.Thread(target=execute_local_job, args=(job,))
            thread.daemon = True
            thread.start()
        elif execution_mode == ExecutionMode.ALPINE:
            # For Alpine, just create SLURM script preview and mark as ready
            job_manager.update_job_status(job.job_id, JobStatus.PENDING)
        
        response = APIResponse(
            success=True,
            message="Job submitted successfully",
            data={'job_id': job.job_id, 'status': job.status.value}
        )
        return jsonify(response.to_dict()), 201
    
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        response = APIResponse(success=False, message="Error submitting job", error=str(e))
        return jsonify(response.to_dict()), 500


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    """Get job status and metadata"""
    try:
        job = job_manager.load_job(job_id)
        if not job:
            response = APIResponse(success=False, message=f"Job not found: {job_id}")
            return jsonify(response.to_dict()), 404
        
        response = APIResponse(
            success=True,
            message="Job status retrieved",
            data=job.to_dict()
        )
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        response = APIResponse(success=False, message="Error retrieving job", error=str(e))
        return jsonify(response.to_dict()), 500


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        status_filter = request.args.get('status', None)
        
        if status_filter:
            try:
                status_filter = JobStatus(status_filter)
            except ValueError:
                response = APIResponse(success=False, message=f"Invalid status: {status_filter}")
                return jsonify(response.to_dict()), 400
        
        jobs = job_manager.list_jobs(status=status_filter, limit=limit)
        
        response = APIResponse(
            success=True,
            message=f"Retrieved {len(jobs)} jobs",
            data={'jobs': [job.to_dict() for job in jobs]}
        )
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        response = APIResponse(success=False, message="Error listing jobs", error=str(e))
        return jsonify(response.to_dict()), 500


@app.route('/api/jobs/<job_id>/results', methods=['GET'])
def get_job_results(job_id: str):
    """List result files for a job"""
    try:
        job = job_manager.load_job(job_id)
        if not job:
            response = APIResponse(success=False, message=f"Job not found: {job_id}")
            return jsonify(response.to_dict()), 404
        
        if job.status != JobStatus.COMPLETED:
            response = APIResponse(success=False, message=f"Job not completed: {job.status.value}")
            return jsonify(response.to_dict()), 400
        
        # List PNG and PDF files
        if job.output_path:
            output_dir = Path(job.output_path)
            files = []
            if output_dir.exists():
                files = [
                    {
                        'name': f.name,
                        'path': str(f.relative_to(output_dir)),
                        'size': f.stat().st_size
                    }
                    for f in output_dir.glob('**/*') if f.is_file()
                ]
        else:
            files = []
        
        response = APIResponse(
            success=True,
            message="Results retrieved",
            data={'job_id': job_id, 'files': files}
        )
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Error retrieving job results: {e}")
        response = APIResponse(success=False, message="Error retrieving results", error=str(e))
        return jsonify(response.to_dict()), 500


@app.route('/api/jobs/<job_id>/download/<path:file_path>', methods=['GET'])
def download_result_file(job_id: str, file_path: str):
    """Download a result file"""
    try:
        job = job_manager.load_job(job_id)
        if not job or not job.output_path:
            return jsonify({'error': 'Job not found'}), 404
        
        full_path = Path(job.output_path) / file_path
        
        # Security check: ensure path is within job output directory
        if not full_path.resolve().is_relative_to(Path(job.output_path).resolve()):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if not full_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(full_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': 'Download failed'}), 500


@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id: str):
    """Cancel or delete a job"""
    try:
        job = job_manager.load_job(job_id)
        if not job:
            response = APIResponse(success=False, message=f"Job not found: {job_id}")
            return jsonify(response.to_dict()), 404
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.status = JobStatus.CANCELLED
            job_manager.save_job(job)
        
        response = APIResponse(success=True, message="Job cancelled")
        return jsonify(response.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        response = APIResponse(success=False, message="Error cancelling job", error=str(e))
        return jsonify(response.to_dict()), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    response = APIResponse(success=False, message="Endpoint not found")
    return jsonify(response.to_dict()), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    response = APIResponse(success=False, message="Internal server error")
    return jsonify(response.to_dict()), 500


if __name__ == '__main__':
    # Clean up old jobs on startup
    job_manager.cleanup_old_jobs(days=30)
    
    # Run server
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"Starting dv2png API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
