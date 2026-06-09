#!/usr/bin/env python
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
