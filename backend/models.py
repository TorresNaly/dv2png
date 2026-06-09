"""
Data models for dv2png jobs and responses
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import uuid


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """Execution mode for jobs"""
    LOCAL = "local"
    ALPINE = "alpine"


@dataclass
class JobParameters:
    """Parameters for an image processing job"""
    your_name: str
    imaged_by: str
    input_directory: str
    output_directory: str
    channel_names: Dict[int, str]
    include_channels: List[str]
    scale_factor: float = 2.0
    brightness_factor: int = 2
    nas_host: Optional[str] = None
    nas_user: Optional[str] = None
    nas_password: Optional[str] = None
    nas_share: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobParameters':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class JobMetadata:
    """Metadata for a processing job"""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    execution_mode: ExecutionMode = ExecutionMode.LOCAL
    parameters: JobParameters = field(default_factory=lambda: JobParameters(
        your_name="", imaged_by="", input_directory="", 
        output_directory="", channel_names={}, include_channels=[]
    ))
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    alpine_job_id: Optional[str] = None  # For Alpine/SLURM jobs
    result_files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON serializable)"""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'execution_mode': self.execution_mode.value,
            'parameters': self.parameters.to_dict(),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'output_path': self.output_path,
            'alpine_job_id': self.alpine_job_id,
            'result_files': self.result_files,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobMetadata':
        """Create from dictionary"""
        data['status'] = JobStatus(data['status'])
        data['execution_mode'] = ExecutionMode(data['execution_mode'])
        data['parameters'] = JobParameters.from_dict(data['parameters'])
        
        # Parse datetime strings
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JobMetadata':
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class APIResponse:
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error': self.error,
        }


@dataclass
class ProcessingConfig:
    """Configuration for image processing"""
    your_name: str
    imaged_by: str
    input_directory: str
    output_directory: str
    channel_names: Dict[int, str]
    include_channels: List[str]
    scale_factor: float = 2.0
    brightness_factor: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
