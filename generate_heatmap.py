"""Generate heatmap from BLE/Wi-Fi scan logs using Folium.

This module processes collected BLE and Wi-Fi scan data to generate an interactive
heatmap visualization showing the density of detected devices across different locations.
"""

import os
from datetime import datetime
from typing import Optional
import logging
import pandas as pd
import folium
from folium.plugins import HeatMap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HeatmapConfig:
    """Configuration settings for heatmap generation."""
    def __init__(self):
        self.db_path: str = os.getenv('HEATMAP_DB_PATH', 'ble_logs.csv')
        self.output_dir: str = os.getenv('HEATMAP_OUTPUT_DIR', '.')
        self.heatmap_radius: int = int(os.getenv('HEATMAP_RADIUS', '15'))
        self.heatmap_blur: int = int(os.getenv('HEATMAP_BLUR', '10'))
        self.heatmap_max_zoom: int = int(os.getenv('HEATMAP_MAX_ZOOM', '1'))
        self.map_zoom_start: int = int(os.getenv('MAP_ZOOM_START', '18'))
        self.map_tiles: str = os.getenv('MAP_TILES', 'OpenStreetMap')

    def get_heatmap_params(self) -> dict:
        """Get heatmap layer parameters.
        
        Returns:
            Dictionary containing heatmap configuration parameters
        """
        return {
            'radius': self.heatmap_radius,
            'blur': self.heatmap_blur,
            'max_zoom': self.heatmap_max_zoom
        }

    def get_map_params(self) -> dict:
        """Get base map parameters.
        
        Returns:
            Dictionary containing map configuration parameters
        """
        return {
            'zoom_start': self.map_zoom_start,
            'tiles': self.map_tiles
        }

class HeatmapGenerator:
    """Class for generating heatmaps from scan data."""
    
    def __init__(self, config: Optional[HeatmapConfig] = None):
        """Initialize the heatmap generator.
        
        Args:
            config: Optional configuration object. If None, default config is used.
        """
        self.config = config or HeatmapConfig()
        self.df: Optional[pd.DataFrame] = None

    def load_data(self) -> bool:
        """Load and validate the scan data.
        
        Returns:
            True if data was successfully loaded and validated, False otherwise
        """
        if not os.path.exists(self.config.db_path):
            logger.error("[!] No data file found at %s", self.config.db_path)
            return False

        try:
            self.df = pd.read_csv(self.config.db_path)
            required_columns = ["lat", "lon"]
            if not all(col in self.df.columns for col in required_columns):
                logger.error("[!] Missing required columns: lat/lon")
                return False

            self.df = self.df.dropna(subset=required_columns)
            if self.df.empty:
                logger.error("[!] No valid geolocation data")
                return False

            # Add data validation
            if not self._validate_coordinates():
                return False

            return True
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            logger.error("Failed to load data: %s", e)
            return False

    def _validate_coordinates(self) -> bool:
        """Validate that coordinates are within reasonable bounds.
        
        Returns:
            True if coordinates are valid, False otherwise
        """
        try:
            # Check latitude bounds (-90 to 90)
            if not self.df['lat'].between(-90, 90).all():
                logger.error("Invalid latitude values detected")
                return False
            
            # Check longitude bounds (-180 to 180)
            if not self.df['lon'].between(-180, 180).all():
                logger.error("Invalid longitude values detected")
                return False
            
            return True
        except (KeyError, AttributeError) as e:
            logger.error("Failed to validate coordinates: %s", e)
            return False

    def generate_heatmap(self) -> Optional[str]:
        """Generate and save the heatmap visualization.
        
        Returns:
            Path to the generated heatmap file if successful, None otherwise
        """
        if not self.load_data():
            return None

        try:
            logger.info("[+] Generating heatmap with %d points...", len(self.df))
            
            # Calculate map center and create base map
            center_lat = self.df["lat"].mean()
            center_lon = self.df["lon"].mean()
            m = folium.Map(
                location=[center_lat, center_lon],
                **self.config.get_map_params()
            )

            # Add heatmap layer with configurable parameters
            HeatMap(
                self.df[["lat", "lon"]].values.tolist(),
                **self.config.get_heatmap_params()
            ).add_to(m)

            # Create output directory if it doesn't exist
            os.makedirs(self.config.output_dir, exist_ok=True)

            # Save the map with timestamp
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                self.config.output_dir,
                f"ble_heatmap_{now}.html"
            )
            m.save(output_file)
            
            logger.info("[✔] Heatmap saved to %s", output_file)
            return output_file

        except (IOError, OSError) as e:
            logger.error("Failed to generate heatmap: %s", e)
            return None

def main() -> None:
    """Main entry point for heatmap generation."""
    config = HeatmapConfig()
    generator = HeatmapGenerator(config)
    generator.generate_heatmap()

if __name__ == "__main__":
    main()
