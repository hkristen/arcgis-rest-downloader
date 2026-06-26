import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd
import requests
from tqdm import tqdm

from .processing import create_cog, create_vrt_from_tiles
from .utils import read_bbox_from_gpkg, cleanup_temp_files


def get_arcgis_services_to_pd(base_url: str) -> pd.DataFrame:
    """Fetches services from ArcGIS REST endpoint.

    Args:
        base_url: Base URL of the ArcGIS REST endpoint.

    Returns:
        DataFrame with services info (category, service_name, year, type, name).
    """
    # Get the response
    response = requests.get(f"{base_url}?f=json")
    data = response.json()

    # Convert to DataFrame
    services_df = pd.DataFrame(data["services"])

    # Clean up the data
    if "name" in services_df.columns:
        # Split the name field if it contains '/'
        if services_df["name"].str.contains("/").any():
            services_df[["category", "service_name"]] = services_df["name"].str.split(
                "/", expand=True
            )
        else:
            services_df["category"] = ""
            services_df["service_name"] = services_df["name"]

    # Add year information if it exists in the name
    services_df["year"] = services_df["service_name"].str.extract(r"(\d{4})")

    # Reorder columns to a more logical sequence
    cols = ["category", "service_name", "year", "type", "name"]
    services_df = services_df[cols]

    # Sort by category and name
    services_df = services_df.sort_values(["category", "service_name"]).reset_index(
        drop=True
    )

    return services_df


def _get_tile_metadata(
    tile_id: Union[str, int], download_url: str
) -> Optional[Tuple[str, dict]]:
    """Resolves the downloadable file parameters for a single tile.

    Args:
        tile_id: Object id of the tile in the ImageServer.
        download_url: URL of the service's download endpoint.

    Returns:
        Tuple of (filename, file_params) for a downloadable tile, or None if the
        tile errored, has no raster files, or is an overview tile.
    """
    download_params = {"rasterIds": str(tile_id), "f": "json"}

    try:
        response_download_one_tile = requests.get(download_url, download_params)
        response_download_one_tile.raise_for_status()
        data_one_tile = response_download_one_tile.json()

        # Skip tiles with errors or missing data
        if "error" in data_one_tile:
            return None
        if "rasterFiles" not in data_one_tile or not data_one_tile["rasterFiles"]:
            return None

        tile_filepath = data_one_tile["rasterFiles"][0]["id"]
        filename = tile_filepath.split("\\")[-1]

        # Skip files that start with "Ov_" -> these are overview tiles we don't need
        if filename.startswith("Ov_"):
            return None

        file_params = {
            "id": tile_filepath,
            "rasterId": str(tile_id),
        }
        return (filename, file_params)

    except Exception as e:
        # Skip any tile that causes problems, but make it visible
        print(f"Warning: could not gather metadata for tile {tile_id}: {e}")
        return None


def _download_single_tile(
    filename: str,
    file_params: dict,
    file_endpoint_url: str,
    output_directory: Union[str, Path],
    image_server_url: str,
    max_retry: int = 5,
) -> Path:
    """Downloads one tile and its metadata to the output directory.

    Args:
        filename: Target filename for the tile.
        file_params: Parameters identifying the file on the file endpoint.
        file_endpoint_url: URL of the service's file endpoint.
        output_directory: Directory to save the tile and its metadata.
        image_server_url: Base ImageServer URL (used for the tile metadata).
        max_retry: Maximum number of retries for failed requests.

    Returns:
        Path to the downloaded tile.
    """
    output_filepath = Path(os.path.join(output_directory, filename))

    # Check if tile is already downloaded
    if os.path.isfile(output_filepath):
        return output_filepath

    def get_request(retries=1):
        try:
            return requests.get(file_endpoint_url, file_params)
        except Exception as e:
            print(f"Request failed for {filename}: {e}")
            if retries >= max_retry:
                raise Exception from e
            retries += 1
            print(f"Retrying {filename} (attempt {retries}) ...")
            return get_request(retries=retries)

    response_file_endpoint_one_tile = get_request()

    # Download tile metadata
    metadata_params = {"f": "pjson"}
    metadata_url = f"{image_server_url}/{file_params['rasterId']}"
    metadata_response = requests.get(metadata_url, params=metadata_params)
    metadata_filename = f"{os.path.splitext(filename)[0]}.json"
    metadata_filepath = os.path.join(output_directory, metadata_filename)

    # Save tile data
    with open(output_filepath, "wb") as output_file:
        output_file.write(response_file_endpoint_one_tile.content)
    # Save tile metadata
    with open(metadata_filepath, "w") as metadata_file:
        json.dump(metadata_response.json(), metadata_file)

    return output_filepath


# Download all raster tiles from one service URL that intersect the bounding box
# service_url = 'https://gis.stmk.gv.at/image/rest/services/OGD_DOP'
def download_raster_tiles_from_service_url(
    service_url: str,
    service_name: str,
    output_directory: Union[str, Path],
    bbox_gpkg_path: Optional[Union[str, Path]] = None,
    max_retry: int = 5,
    outSRS: int = 32633,
    parallel: bool = False,
    max_workers: int = 10,
) -> List[Path]:
    """Downloads raster tiles from service URL intersecting bounding box.

    Args:
        service_url: Base URL of the service.
        service_name: Name of service to download tiles from.
        output_directory: Directory to save downloaded tiles.
        bbox_gpkg_path: Path to GeoPackage file for bounding box. If None, all
            tiles of the service are downloaded.
        max_retry: Maximum number of retries for failed requests.
        outSRS: Output spatial reference system.
        parallel: Whether to gather metadata and download tiles in parallel.
            Recommended when downloading large areas (e.g. a whole service).
        max_workers: Maximum number of parallel workers (only used if parallel).

    Returns:
        List of paths to downloaded raster tiles.
    """
    query_url = f"{service_url}/{service_name}/ImageServer/query"
    download_url = f"{service_url}/{service_name}/ImageServer/download"
    file_endpoint_url = f"{service_url}/{service_name}/ImageServer/file"
    image_server_url = f"{service_url}/{service_name}/ImageServer"

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    print(f"Downloading tiles from service: {service_name}")

    if bbox_gpkg_path is not None:
        bbox = read_bbox_from_gpkg(bbox_gpkg_path)
        query_params = {
            "where": "1=1",
            "geometry": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",  # bbox returns tuple of (minx,miny,maxx,maxy)
            "geometryType": "esriGeometryEnvelope",
            "inSR": 32633,  # Specifying input coordinate system
            "spatialRel": "esriSpatialRelIntersects",
            "returnGeometry": "false",
            "returnIdsOnly": "true",
            "outSR": outSRS,  # Specifying output coordinate system
            "f": "json",
        }
    else:
        # if no bbox is provided, download all tiles
        query_params = {"where": "1=1", "f": "json", "returnIdsOnly": "true"}

    response_query_all_tiles_one_service = requests.get(query_url, params=query_params)
    data_all_tiles_one_service = response_query_all_tiles_one_service.json()
    if not data_all_tiles_one_service["objectIds"]:
        raise RuntimeError("No data available with these parameters.")

    # Download service metadata
    metadata_params = {"f": "pjson"}
    metadata_response = requests.get(image_server_url, params=metadata_params)
    metadata_filename = f"{service_name}.json"
    metadata_filepath = os.path.join(output_directory, metadata_filename)
    with open(metadata_filepath, "w") as metadata_file:
        json.dump(metadata_response.json(), metadata_file)
    print(f"Metadata saved to {metadata_filepath}")

    object_ids = data_all_tiles_one_service["objectIds"]
    total_tiles = len(object_ids)

    # Gather the file parameters for every relevant tile
    print("\n Gathering tile information...")
    tile_infos: List[Tuple[str, dict]] = []
    if parallel and total_tiles > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_get_tile_metadata, tile_id, download_url)
                for tile_id in object_ids
            ]
            for future in tqdm(
                as_completed(futures), total=total_tiles, desc="Processing tiles"
            ):
                result = future.result()
                if result is not None:
                    tile_infos.append(result)
    else:
        for tile_id in tqdm(object_ids, desc="Processing tiles"):
            result = _get_tile_metadata(tile_id, download_url)
            if result is not None:
                tile_infos.append(result)

    # Deduplicate by filename (preserves original dict-based behaviour)
    file_param_list = {filename: file_params for filename, file_params in tile_infos}

    output_files: List[Path] = []

    # Download each tile and write to output directory
    print("\n Downloading tiles...")
    if parallel and len(file_param_list) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_filename = {
                executor.submit(
                    _download_single_tile,
                    filename,
                    file_params,
                    file_endpoint_url,
                    output_directory,
                    image_server_url,
                    max_retry,
                ): filename
                for filename, file_params in file_param_list.items()
            }
            for future in tqdm(
                as_completed(future_to_filename),
                total=len(future_to_filename),
                desc="Downloading tiles",
            ):
                filename = future_to_filename[future]
                try:
                    output_files.append(future.result())
                except Exception as exc:
                    print(f"Download failed for {filename}: {exc}")
    else:
        for filename, file_params in tqdm(
            file_param_list.items(), desc="Downloading tiles"
        ):
            try:
                output_files.append(
                    _download_single_tile(
                        filename,
                        file_params,
                        file_endpoint_url,
                        output_directory,
                        image_server_url,
                        max_retry,
                    )
                )
            except Exception as exc:
                print(f"Download failed for {filename}: {exc}")

    print(f"Downloaded {len(output_files)} tiles to {output_directory}")

    return output_files


def download_and_create_cog(
    service_url: str,
    service_name: str,
    output_path: Union[str, Path],
    bbox_gpkg_path: Union[str, Path],
    raw_data_folder: Optional[Union[str, Path]] = None,
    max_retry: int = 5,
    outSRS: int = 32633,
    out_nodata_value: Optional[Union[float, int]] = None,
    parallel: bool = False,
    max_workers: int = 10,
) -> None:
    """Downloads raster tiles and creates a COG.

    Args:
        service_url: Base URL of the service.
        service_name: Name of service to download tiles from.
        output_path: Path to save final COG file.
        bbox_gpkg_path: Path to GeoPackage file for bounding box.
        raw_data_folder: Directory to save raw data.
        max_retry: Maximum number of retries for failed requests.
        outSRS: Output spatial reference system.
        out_nodata_value: Nodata value for output (pixel values unchanged).
        parallel: Whether to download tiles in parallel.
        max_workers: Maximum number of parallel workers (only used if parallel).

    Raises:
        Exception: If error occurs during processing.
    """
    # Set tile and vrt file paths
    if not raw_data_folder:
        # Create temporary directory
        raw_data_folder = tempfile.mkdtemp()
        vrt_path = raw_data_folder / (service_name.lower() + ".vrt")
        cleanup = True
    else:
        Path(raw_data_folder).mkdir(parents=True, exist_ok=True)
        vrt_path = Path(raw_data_folder).parent / (service_name.lower() + ".vrt")
        cleanup = False

    # Create output file path
    Path(output_path).parent.mkdir(exist_ok=True)

    try:
        # Download tiles
        tiles = download_raster_tiles_from_service_url(
            service_url=service_url,
            service_name=service_name,
            output_directory=raw_data_folder,
            bbox_gpkg_path=bbox_gpkg_path,
            max_retry=max_retry,
            outSRS=outSRS,
            parallel=parallel,
            max_workers=max_workers,
        )

        # Create VRT
        print("Creating VRT...")
        create_vrt_from_tiles(tiles, vrt_path)

        # Convert to COG
        print("Converting to COG...")
        create_cog(
            vrt_path,
            output_path,
            outSRS=outSRS,
            out_nodata_value=out_nodata_value,
        )

        # Only cleanup after successful COG creation and verification if raw data is not to be saved
        if cleanup:
            cleanup_temp_files(tiles, raw_data_folder, vrt_path)

    except Exception as e:
        # In case of error, keep temporary files and re-raise the exception
        print(f"Error during processiing: {e}")
        print(f"Raster Tiles preserved in: {raw_data_folder}")
        raise
    print("Done!")
