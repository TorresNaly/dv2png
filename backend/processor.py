"""
FISH Image Converter - Core Processing Module
Extracted from dv2png.ipynb for modular use
"""

import os
import glob
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF

# Import bigfish components
try:
    import bigfish.stack as stack
except (ImportError, ModuleNotFoundError) as e:
    # Try workaround for scikit-image compatibility
    try:
        from skimage.morphology import square
        import bigfish.stack as stack
    except Exception:
        raise ImportError("bigfish package is required. Install it with: pip install big-fish")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """Main processor for FISH image conversion"""
    
    def __init__(self, config: Dict):
        """
        Initialize processor with configuration
        
        Args:
            config: Dictionary containing:
                - input_directory: Path to raw image files
                - output_directory: Path to save results
                - channel_names: Dict mapping channel indices to names
                - include_channels: List of channels to include in composite
                - your_name: Name of processor
                - imaged_by: Name of person who imaged
                - scale_factor: Brightness multiplier for channels
                - brightness_factor: Final brightness adjustment
        """
        self.config = config
        self.input_directory = Path(config['input_directory'])
        self.output_directory = Path(config['output_directory'])
        self.channel_names = config.get('channel_names', {
            0: 'Cy5',
            1: 'mCherry',
            2: 'FITC',
            3: 'DAPI'
        })
        self.include_channels = config.get('include_channels', [])
        self.your_name = config.get('your_name', 'Unknown')
        self.imaged_by = config.get('imaged_by', 'Unknown')
        self.scale_factor = config.get('scale_factor', 2.0)
        self.brightness_factor = config.get('brightness_factor', 2)
        
        # Tracking
        self.all_image_color_stacks = []
        self.all_bf_stacks = []
        self.subdirectories = []
        self.image_color_paths = []
        self.bf_paths = []
        
        logger.info(f"ImageProcessor initialized with output directory: {self.output_directory}")
    
    def validate_config(self) -> Tuple[bool, str]:
        """
        Validate configuration and directories
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.input_directory.exists():
            return False, f"Input directory does not exist: {self.input_directory}"
        
        if not self.input_directory.is_dir():
            return False, f"Input path is not a directory: {self.input_directory}"
        
        return True, ""
    
    def list_dv_files(self) -> Tuple[List[str], List[str]]:
        """
        List all .dv files in input directory
        
        Returns:
            Tuple of (color_image_paths, bf_image_paths)
        """
        self.image_color_paths = []
        self.bf_paths = []
        
        for file_path in self.input_directory.glob('*_R3D_D3D.dv'):
            self.image_color_paths.append(str(file_path))
        
        for file_path in self.input_directory.glob('*_R3D_REF.dv'):
            self.bf_paths.append(str(file_path))
        
        self.image_color_paths = sorted(self.image_color_paths)
        self.bf_paths = sorted(self.bf_paths)
        
        logger.info(f"Found {len(self.image_color_paths)} color images and {len(self.bf_paths)} BF images")
        
        return self.image_color_paths, self.bf_paths
    
    def read_image_stacks(self) -> bool:
        """
        Read all image stacks from files
        
        Returns:
            Success status
        """
        try:
            self.all_image_color_stacks = []
            self.subdirectories = []
            self.all_bf_stacks = []
            
            # Read color images
            for image_color_path in self.image_color_paths:
                image_color_stack = stack.read_dv(image_color_path, sanity_check=True)
                self.all_image_color_stacks.append(image_color_stack)
                
                # Extract subdirectory name from filename
                file_name = Path(image_color_path).stem
                parts = file_name.split('_')
                numeric_part = None
                for i, part in enumerate(parts):
                    if part == 'R3D':
                        numeric_part = parts[i - 1]
                        break
                if numeric_part:
                    self.subdirectories.append(numeric_part)
            
            # Read BF images
            for bf_path in self.bf_paths:
                bf_stack = stack.read_dv(bf_path, sanity_check=True)
                self.all_bf_stacks.append(bf_stack)
            
            logger.info(f"Successfully read {len(self.all_image_color_stacks)} image stacks")
            return True
        
        except Exception as e:
            logger.error(f"Error reading image stacks: {e}")
            return False
    
    @staticmethod
    def normalize(img: np.ndarray) -> np.ndarray:
        """Normalize image to [0, 1] range"""
        if img.max() > 0:
            return (img - img.min()) / (img.max() - img.min())
        return img
    
    def process_images(self) -> bool:
        """
        Process all image stacks: extract channels, create composites, save PNGs
        
        Returns:
            Success status
        """
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            
            for i, stack_data in enumerate(self.all_image_color_stacks):
                image_colors = stack_data
                
                # Create subdirectory for outputs
                output_subdirectory = self.output_directory / str(self.subdirectories[i])
                output_subdirectory.mkdir(parents=True, exist_ok=True)
                
                channel_dict = {}
                
                # Extract and save individual channels
                for channel_index in range(image_colors.shape[0]):
                    current_image = image_colors[channel_index, :, :]
                    
                    # Get channel name
                    channel_name = self.channel_names.get(channel_index, f"Channel_{channel_index}")
                    
                    # Save each channel (max projection in z-axis for 3D)
                    max_projection = np.max(current_image, axis=0)
                    plot_filename = output_subdirectory / f"{self.subdirectories[i]}_{channel_name}_deconvolved.png"
                    plt.imsave(str(plot_filename), max_projection, cmap='gray')
                    
                    # Store channel for composite if selected
                    if channel_name in self.include_channels:
                        channel_dict[channel_name] = self.normalize(max_projection)
                
                # Create composite image if selected channels exist
                if channel_dict:
                    composite = self._create_composite(channel_dict)
                    if composite is not None:
                        composite_filename = output_subdirectory / f"{self.subdirectories[i]}_composite.png"
                        plt.imsave(str(composite_filename), composite)
                        logger.info(f"Saved composite image: {composite_filename}")
            
            logger.info(f"Successfully processed {len(self.subdirectories)} images")
            return True
        
        except Exception as e:
            logger.error(f"Error processing images: {e}")
            return False
    
    def _create_composite(self, channel_dict: Dict[str, np.ndarray]) -> Optional[np.ndarray]:
        """
        Create RGB composite image from selected channels
        
        Args:
            channel_dict: Dictionary mapping channel names to normalized images
            
        Returns:
            RGB composite image or None if creation failed
        """
        try:
            # Ensure all channels are the same size
            if len(set([img.shape for img in channel_dict.values()])) > 1:
                logger.warning(f"Channel size mismatch: {[img.shape for img in channel_dict.values()]}")
                return None
            
            # Initialize RGB image
            first_channel = next(iter(channel_dict.values()))
            composite = np.zeros((first_channel.shape[0], first_channel.shape[1], 3))
            
            # Assign colors based on selected channels
            if 'Cy5' in channel_dict:
                cy5_channel = self.normalize(channel_dict['Cy5']) * self.scale_factor
                composite[..., 0] = np.maximum(composite[..., 0], cy5_channel)
            
            if 'mCherry' in channel_dict:
                mcherry_channel = self.normalize(channel_dict['mCherry']) * self.scale_factor
                composite[..., 0] = np.maximum(composite[..., 0], mcherry_channel)
                composite[..., 2] = np.maximum(composite[..., 2], mcherry_channel)
            
            if 'FITC' in channel_dict:
                fitc_channel = self.normalize(channel_dict['FITC'])
                composite[..., 1] = np.maximum(composite[..., 1], fitc_channel)
            
            if 'DAPI' in channel_dict:
                dapi_channel = self.normalize(channel_dict['DAPI'])
                composite[..., 2] = np.maximum(composite[..., 2], dapi_channel)
            
            # Normalize and apply brightness
            composite = np.clip(composite / composite.max(), 0, 1) if composite.max() > 0 else composite
            composite = np.clip(composite * self.brightness_factor, 0, 1)
            
            return composite
        
        except Exception as e:
            logger.error(f"Error creating composite: {e}")
            return None
    
    def generate_pdf_report(self) -> bool:
        """
        Generate PDF report with all processed images
        
        Returns:
            Success status
        """
        try:
            pdf_filename = self.output_directory / "report.pdf"
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Find and read README file
            readme_content = "No README file found."
            readme_file = None
            for file_path in self.input_directory.glob('*README*'):
                readme_file = file_path
                break
            
            if readme_file and readme_file.exists():
                try:
                    with open(readme_file, "r") as f:
                        readme_content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read README: {e}")
            
            # Add cover letter
            self._add_cover_letter(pdf, readme_content)
            
            # Define image order for PDF
            image_order = list(self.channel_names.values()) + ["composite"]
            
            # Add images page
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            for subdirectory in sorted(self.subdirectories):
                pdf.cell(200, 10, txt=f"Image ID: {Path(self.input_directory).name}_{subdirectory}", ln=True, align='L')
                pdf.ln(5)
                
                # Get PNG files in subdirectory
                subdirectory_path = self.output_directory / subdirectory
                png_files = list(subdirectory_path.glob('*.png'))
                
                if not png_files:
                    continue
                
                # Sort by image order
                png_files_sorted = sorted(png_files, 
                    key=lambda x: image_order.index(x.stem.split('_')[1]) 
                    if x.stem.split('_')[1] in image_order else len(image_order))
                
                # Add images to PDF
                max_columns = 5
                num_columns = min(len(png_files_sorted), max_columns)
                column_width = 190 / num_columns
                
                for i, png_file in enumerate(png_files_sorted):
                    x_position = pdf.get_x() + i % num_columns * column_width
                    y_position = pdf.get_y() + int(i / num_columns) * 20
                    
                    try:
                        pdf.image(str(png_file), x=x_position, y=y_position, w=column_width)
                    except Exception as e:
                        logger.warning(f"Could not add image {png_file}: {e}")
                
                pdf.ln(80 * ((len(png_files_sorted) - 1) // num_columns + 1))
            
            # Save PDF
            pdf.output(str(pdf_filename))
            logger.info(f"PDF report created: {pdf_filename}")
            return True
        
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def _add_cover_letter(self, pdf: FPDF, readme_content: str):
        """Add cover letter page to PDF"""
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        
        experiment_id = Path(self.input_directory).name
        pdf.cell(100, 10, txt=f"Experiment Title: {experiment_id}", ln=True, align='C')
        pdf.ln(2)
        
        today_date = datetime.now().strftime("%B %d, %Y")
        details = [
            f"Date of processing: {today_date}",
            f"Imaged by: {self.imaged_by}",
            f"Processed by: {self.your_name}",
            f"Channels: {', '.join(self.channel_names.values())}",
            f"Channels in composite: {', '.join(self.include_channels)}",
            " ",
            "README file:"
        ]
        
        for detail in details:
            pdf.cell(200, 10, txt=detail, ln=True, align='L')
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, txt=readme_content)
        pdf.ln(10)
    
    def run_full_pipeline(self) -> Tuple[bool, str]:
        """
        Run complete processing pipeline
        
        Returns:
            Tuple of (success_status, message)
        """
        try:
            # Validate
            is_valid, error_msg = self.validate_config()
            if not is_valid:
                return False, error_msg
            
            # List files
            self.list_dv_files()
            if not self.image_color_paths:
                return False, "No .dv image files found in input directory"
            
            # Read stacks
            if not self.read_image_stacks():
                return False, "Failed to read image stacks"
            
            # Process images
            if not self.process_images():
                return False, "Failed to process images"
            
            # Generate PDF
            if not self.generate_pdf_report():
                logger.warning("PDF generation failed, but images were saved")
            
            message = f"Successfully processed {len(self.subdirectories)} images. Results saved to {self.output_directory}"
            return True, message
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return False, str(e)
