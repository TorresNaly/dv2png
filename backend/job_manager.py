"""
Job manager for storing and retrieving job metadata
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from models import JobMetadata, JobStatus

logger = logging.getLogger(__name__)


class JobManager:
    """Manages job storage and retrieval"""
    
    def __init__(self, storage_dir: str = "./jobs"):
        """
        Initialize job manager
        
        Args:
            storage_dir: Directory to store job data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.storage_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
    
    def save_job(self, job: JobMetadata) -> bool:
        """
        Save job metadata to disk
        
        Args:
            job: JobMetadata instance
            
        Returns:
            Success status
        """
        try:
            # Create job output directory
            job_output_dir = self.storage_dir / job.job_id
            job_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save metadata
            metadata_file = self.metadata_dir / f"{job.job_id}.json"
            with open(metadata_file, 'w') as f:
                f.write(job.to_json())
            
            logger.info(f"Saved job metadata: {metadata_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            return False
    
    def load_job(self, job_id: str) -> Optional[JobMetadata]:
        """
        Load job metadata from disk
        
        Args:
            job_id: Job ID
            
        Returns:
            JobMetadata instance or None if not found
        """
        try:
            metadata_file = self.metadata_dir / f"{job_id}.json"
            if not metadata_file.exists():
                logger.warning(f"Job metadata not found: {job_id}")
                return None
            
            with open(metadata_file, 'r') as f:
                return JobMetadata.from_json(f.read())
        
        except Exception as e:
            logger.error(f"Error loading job {job_id}: {e}")
            return None
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[JobMetadata]:
        """
        List all jobs, optionally filtered by status
        
        Args:
            status: Filter by JobStatus (optional)
            limit: Maximum number of jobs to return
            
        Returns:
            List of JobMetadata instances
        """
        try:
            jobs = []
            metadata_files = sorted(self.metadata_dir.glob("*.json"), 
                                   key=lambda x: x.stat().st_mtime, reverse=True)
            
            for metadata_file in metadata_files[:limit]:
                job = self.load_job(metadata_file.stem)
                if job:
                    if status is None or job.status == status:
                        jobs.append(job)
            
            return jobs
        
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         error_message: Optional[str] = None) -> bool:
        """
        Update job status
        
        Args:
            job_id: Job ID
            status: New JobStatus
            error_message: Optional error message
            
        Returns:
            Success status
        """
        try:
            job = self.load_job(job_id)
            if not job:
                return False
            
            job.status = status
            if error_message:
                job.error_message = error_message
            
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.now()
            elif status == JobStatus.COMPLETED and not job.completed_at:
                job.completed_at = datetime.now()
            elif status == JobStatus.FAILED and not job.completed_at:
                job.completed_at = datetime.now()
            
            return self.save_job(job)
        
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False
    
    def get_job_output_dir(self, job_id: str) -> Path:
        """Get output directory for a job"""
        return self.storage_dir / job_id / "output"
    
    def get_job_results_dir(self, job_id: str) -> Path:
        """Get results directory for a job (images, PDFs, etc.)"""
        return self.storage_dir / job_id / "results"
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Delete job data older than specified days
        
        Args:
            days: Delete jobs older than this many days
            
        Returns:
            Number of jobs deleted
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for job_file in self.metadata_dir.glob("*.json"):
                job = self.load_job(job_file.stem)
                if job and job.created_at < cutoff_time:
                    # Delete job directory
                    job_dir = self.storage_dir / job.job_id
                    if job_dir.exists():
                        import shutil
                        shutil.rmtree(job_dir)
                    
                    # Delete metadata
                    job_file.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old jobs")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {e}")
            return 0
