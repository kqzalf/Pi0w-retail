"""Generate heatmap from BLE/Wi-Fi scan logs using Folium.

This module processes collected BLE and Wi-Fi scan data to generate an interactive
heatmap visualization showing the density of detected devices across different locations.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
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
        self.DB_PATH: str = os.getenv('HEATMAP_DB_PATH', 'ble_logs.csv')
        self.OUTPUT_DIR: str = os.getenv('HEATMAP_OUTPUT_DIR', '.')
        self.HEATMAP_RADIUS: int = int(os.getenv('HEATMAP_RADIUS', '15'))
        self.HEATMAP_BLUR: int = int(os.getenv('HEATMAP_BLUR', '10'))
        self.HEATMAP_MAX_ZOOM: int = int(os.getenv('HEATMAP_MAX_ZOOM', '1'))
        self.MAP_ZOOM_START: int = int(os.getenv('MAP_ZOOM_START', '18'))
        self.MAP_TILES: str = os.getenv('MAP_TILES', 'OpenStreetMap')

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
        if not os.path.exists(self.config.DB_PATH):
            logger.error(f"[!] No data file found at {self.config.DB_PATH}")
            return False

        try:
            self.df = pd.read_csv(self.config.DB_PATH)
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
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
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
        except Exception as e:
            logger.error(f"Failed to validate coordinates: {e}")
            return False

    def generate_heatmap(self) -> Optional[str]:
        """Generate and save the heatmap visualization.
        
        Returns:
            Path to the generated heatmap file if successful, None otherwise
        """
        if not self.load_data():
            return None

        try:
            logger.info(f"[+] Generating heatmap with {len(self.df)} points...")
            
            # Calculate map center and create base map
            center_lat = self.df["lat"].mean()
            center_lon = self.df["lon"].mean()
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=self.config.MAP_ZOOM_START,
                tiles=self.config.MAP_TILES
            )

            # Add heatmap layer with configurable parameters
            HeatMap(
                self.df[["lat", "lon"]].values.tolist(),
                radius=self.config.HEATMAP_RADIUS,
                blur=self.config.HEATMAP_BLUR,
                max_zoom=self.config.HEATMAP_MAX_ZOOM
            ).add_to(m)

            # Create output directory if it doesn't exist
            os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)

            # Save the map with timestamp
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                self.config.OUTPUT_DIR,
                f"ble_heatmap_{now}.html"
            )
            m.save(output_file)
            
            logger.info(f"[✔] Heatmap saved to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to generate heatmap: {e}")
            return None

def main() -> None:
    """Main entry point for heatmap generation."""
    config = HeatmapConfig()
    generator = HeatmapGenerator(config)
    generator.generate_heatmap()

if __name__ == "__main__":
    main()
