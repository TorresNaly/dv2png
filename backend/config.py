"""
Configuration management for dv2png application
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class Config:
    """Configuration manager for dv2png"""
    
    # Default NAS settings (customize for your lab)
    DEFAULT_NAS_CONFIG = {
        'nas_host': '',
        'nas_user': '',
        'nas_password': '',
        'nas_share': '',
    }
    
    # Default channel configuration
    DEFAULT_CHANNELS = {
        0: 'Cy5',
        1: 'mCherry',
        2: 'FITC',
        3: 'DAPI'
    }
    
    # Default processing parameters
    DEFAULT_PROCESSING = {
        'scale_factor': 2.0,
        'brightness_factor': 2,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize config, optionally loading from file
        
        Args:
            config_file: Path to YAML config file (optional)
        """
        self.config_file = config_file
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        config = {
            'nas': self.DEFAULT_NAS_CONFIG.copy(),
            'channels': self.DEFAULT_CHANNELS.copy(),
            'processing': self.DEFAULT_PROCESSING.copy(),
        }
        
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = yaml.safe_load(f)
                    if loaded:
                        config.update(loaded)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        return config
    
    def save_config(self, output_file: str):
        """Save current config to YAML file"""
        with open(output_file, 'w') as f:
            yaml.dump(self.config_data, f, default_flow_style=False)
    
    def get_nas_config(self) -> Dict[str, str]:
        """Get NAS configuration"""
        return self.config_data.get('nas', self.DEFAULT_NAS_CONFIG)
    
    def get_channels(self) -> Dict[int, str]:
        """Get channel configuration"""
        return self.config_data.get('channels', self.DEFAULT_CHANNELS)
    
    def get_processing_defaults(self) -> Dict[str, float]:
        """Get default processing parameters"""
        return self.config_data.get('processing', self.DEFAULT_PROCESSING)
    
    def update_nas_config(self, **kwargs):
        """Update NAS configuration"""
        self.config_data['nas'].update(kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export full configuration as dict"""
        return self.config_data.copy()


def create_default_config_file(output_path: str):
    """Create a default config file template"""
    config = {
        'nas': Config.DEFAULT_NAS_CONFIG,
        'channels': Config.DEFAULT_CHANNELS,
        'processing': Config.DEFAULT_PROCESSING,
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Default config file created at {output_path}")


# Singleton config instance
_config_instance = None

def get_config(config_file: Optional[str] = None) -> Config:
    """Get or create config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance
