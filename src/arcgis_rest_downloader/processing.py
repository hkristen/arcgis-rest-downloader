import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Union


def create_vrt_from_tiles(tile_paths: List[Union[str, Path]], output_vrt: str) -> None:
    """Creates VRT file from raster tiles.

    Args:
        tile_paths: List of paths to raster tiles.
        output_vrt: Path to output VRT file.
    """
    # Convert all paths to strings
    tile_paths = [str(p) for p in tile_paths]

    # Create VRT using gdalbuildvrt
    cmd = ["gdalbuildvrt", output_vrt] + tile_paths
    subprocess.run(cmd, check=True)


def create_cog(
    input_path: str,
    output_path: str,
    outSRS: int = 32633,
    out_nodata_value: Optional[Union[float, int]] = None,
) -> None:
    """Creates Cloud Optimized GeoTIFF (COG) from input raster.

    Args:
        input_path: Path to input raster file.
        output_path: Path to output COG file.
        outSRS: Output spatial reference system.
        out_nodata_value: Nodata value for output.
    """
    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define intermediate file paths
        temp_vrt = os.path.join(temp_dir, "temp.vrt")
        temp_tif = os.path.join(temp_dir, "temp.tif")

        # Create VRT with specified SRS
        vrt_cmd = [
            "gdalwarp",
            "-of",
            "VRT",
            "-t_srs",
            f"EPSG:{outSRS}",
            input_path,
            temp_vrt,
        ]
        subprocess.run(vrt_cmd, check=True)

        # Convert to GeoTIFF with compression
        tif_cmd = [
            "gdal_translate",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=LZW",
        ]

        if out_nodata_value is not None:
            tif_cmd.extend(["-a_nodata", str(out_nodata_value)])

        tif_cmd.extend([temp_vrt, temp_tif])
        subprocess.run(tif_cmd, check=True)

        # Add overviews
        overview_cmd = [
            "gdaladdo",
            "-r",
            "average",
            temp_tif,
            "2",
            "4",
            "8",
            "16",
            "32",
        ]
        subprocess.run(overview_cmd, check=True)

        # Create final COG
        cog_cmd = [
            "gdal_translate",
            "-of",
            "COG",
            "-co",
            "COMPRESS=LZW",
            "-co",
            "OVERVIEWS=IGNORE_EXISTING",
            temp_tif,
            output_path,
        ]
        subprocess.run(cog_cmd, check=True)
