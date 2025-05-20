import os
import shutil
from pathlib import Path
from typing import Tuple, Union, List
import geopandas as gpd


def read_bbox_from_gpkg(
    gpkg_path: Union[str, Path],
) -> Tuple[float, float, float, float]:
    """Reads bounding box from GeoPackage file.

    Args:
        gpkg_path: Path to GeoPackage file.

    Returns:
        Bounding box coordinates (xmin, ymin, xmax, ymax).
    """
    gdf = gpd.read_file(gpkg_path)
    return gdf.total_bounds


def cleanup_temp_files(temp_files: List[str], temp_dir: str, vrt_path: str) -> None:
    """Removes temporary files and directories.

    Args:
        temp_files: List of file paths to delete.
        temp_dir: Path to temporary directory to remove.
        vrt_path: Path to VRT file to delete.
    """
    if temp_files:
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not remove {temp_file}: {e}")
    try:
        if os.path.exists(vrt_path):
            os.remove(vrt_path)
    except Exception as e:
        print(f"Warning: Could not remove VRT: {e}")
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(
                temp_dir
            )  # This will remove the directory and all its contents
    except Exception as e:
        print(f"Warning: Could not remove temp directory: {e}")
