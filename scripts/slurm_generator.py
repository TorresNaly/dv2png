"""
SLURM script generator for Alpine HPC
"""

from pathlib import Path
from typing import Dict, Any
from models import JobParameters


class SlurmScriptGenerator:
    """Generate SLURM submission scripts for Alpine HPC"""
    
    # Default SLURM settings
    DEFAULT_SLURM_CONFIG = {
        'time': '02:00:00',
        'nodes': 1,
        'tasks_per_node': 1,
        'cpus_per_task': 4,
        'mem': '16G',
        'partition': 'amethyst',  # Alpine partition
    }
    
    def __init__(self, job_id: str, parameters: JobParameters, 
                 slurm_config: Dict[str, Any] = None):
        """
        Initialize generator
        
        Args:
            job_id: Job identifier
            parameters: JobParameters instance
            slurm_config: Override default SLURM settings
        """
        self.job_id = job_id
        self.parameters = parameters
        self.slurm_config = {**self.DEFAULT_SLURM_CONFIG, **(slurm_config or {})}
    
    def generate_script(self, python_processor_path: str = "processor.py") -> str:
        """
        Generate SLURM submission script
        
        Args:
            python_processor_path: Path to processor.py on Alpine
            
        Returns:
            SLURM script as string
        """
        script = self._generate_header()
        script += self._generate_setup()
        script += self._generate_execution(python_processor_path)
        
        return script
    
    def _generate_header(self) -> str:
        """Generate SLURM header with directives"""
        header = "#!/bin/bash\n"
        header += f"#SBATCH --job-name=dv2png_{self.job_id[:8]}\n"
        header += f"#SBATCH --time={self.slurm_config['time']}\n"
        header += f"#SBATCH --nodes={self.slurm_config['nodes']}\n"
        header += f"#SBATCH --tasks-per-node={self.slurm_config['tasks_per_node']}\n"
        header += f"#SBATCH --cpus-per-task={self.slurm_config['cpus_per_task']}\n"
        header += f"#SBATCH --mem={self.slurm_config['mem']}\n"
        header += f"#SBATCH --partition={self.slurm_config['partition']}\n"
        header += f"#SBATCH --output=logs/dv2png_{self.job_id[:8]}_%j.log\n"
        header += f"#SBATCH --error=logs/dv2png_{self.job_id[:8]}_%j.err\n"
        header += "\n"
        
        return header
    
    def _generate_setup(self) -> str:
        """Generate setup commands"""
        setup = "# Load required modules\n"
        setup += "module load anaconda\n"
        setup += "\n"
        setup += "# Activate conda environment (create one if needed)\n"
        setup += "conda activate dv2png\n"
        setup += "\n"
        setup += "# Create output directory\n"
        setup += f"mkdir -p {Path(self.parameters.output_directory).parent}/logs\n"
        setup += "\n"
        
        return setup
    
    def _generate_execution(self, processor_path: str) -> str:
        """Generate Python execution commands"""
        # Build parameter dict string
        params_dict = (
            "{\n"
            f"    'input_directory': '{self.parameters.input_directory}',\n"
            f"    'output_directory': '{self.parameters.output_directory}',\n"
            f"    'your_name': '{self.parameters.your_name}',\n"
            f"    'imaged_by': '{self.parameters.imaged_by}',\n"
            f"    'channel_names': {self.parameters.channel_names},\n"
            f"    'include_channels': {self.parameters.include_channels},\n"
            f"    'scale_factor': {self.parameters.scale_factor},\n"
            f"    'brightness_factor': {self.parameters.brightness_factor},\n"
            "}"
        )
        
        execution = "# Run image processing\n"
        execution += f"python {processor_path} \\\n"
        execution += f"    --input '{self.parameters.input_directory}' \\\n"
        execution += f"    --output '{self.parameters.output_directory}' \\\n"
        execution += f"    --your-name '{self.parameters.your_name}' \\\n"
        execution += f"    --imaged-by '{self.parameters.imaged_by}' \\\n"
        execution += f"    --include-channels {','.join(self.parameters.include_channels)}\n"
        execution += "\n"
        execution += "# Check exit status\n"
        execution += "if [ $? -eq 0 ]; then\n"
        execution += "    echo 'Processing completed successfully'\n"
        execution += "else\n"
        execution += "    echo 'Processing failed with exit code' $?\n"
        execution += "    exit 1\n"
        execution += "fi\n"
        
        return execution
    
    def save_script(self, output_file: str):
        """Save script to file"""
        script = self.generate_script()
        with open(output_file, 'w') as f:
            f.write(script)
        
        # Make executable
        Path(output_file).chmod(0o755)
        
        return output_file


def generate_python_runner() -> str:
    """
    Generate standalone Python runner script for Alpine
    This allows running the processor without Flask
    """
    runner = '''#!/usr/bin/env python
"""
dv2png standalone runner for Alpine HPC
Run as: python processor_runner.py --input /path/to/input --output /path/to/output ...
"""

import argparse
import sys
import logging
from processor import ImageProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='FISH Image Converter')
    parser.add_argument('--input', required=True, help='Input directory')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--your-name', required=True, help='Processor name')
    parser.add_argument('--imaged-by', required=True, help='Imager name')
    parser.add_argument('--cy5', default='Cy5', help='Cy5 channel name')
    parser.add_argument('--mcherry', default='mCherry', help='mCherry channel name')
    parser.add_argument('--fitc', default='FITC', help='FITC channel name')
    parser.add_argument('--dapi', default='DAPI', help='DAPI channel name')
    parser.add_argument('--include-channels', required=True, help='Channels to include (comma-separated)')
    parser.add_argument('--scale-factor', type=float, default=2.0, help='Channel scale factor')
    parser.add_argument('--brightness-factor', type=int, default=2, help='Final brightness factor')
    
    args = parser.parse_args()
    
    config = {
        'input_directory': args.input,
        'output_directory': args.output,
        'your_name': args.your_name,
        'imaged_by': args.imaged_by,
        'channel_names': {
            0: args.cy5,
            1: args.mcherry,
            2: args.fitc,
            3: args.dapi,
        },
        'include_channels': [c.strip() for c in args.include_channels.split(',')],
        'scale_factor': args.scale_factor,
        'brightness_factor': args.brightness_factor,
    }
    
    processor = ImageProcessor(config)
    success, message = processor.run_full_pipeline()
    
    if success:
        logger.info(message)
        sys.exit(0)
    else:
        logger.error(message)
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
    return runner
