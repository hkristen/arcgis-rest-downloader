"""Download the whole GIS Steiermark orthophoto archive (all tiles, no bbox).

This wrapper downloads every tile of one or more ArcGIS ImageServer services to
a local directory, in parallel. It is meant for grabbing a complete archive
(e.g. all of Styria) rather than a single region of interest.

No COGs are created: the script only fetches the original tiles plus their
metadata, so you keep full control over any later merging / processing.

Example:
    python scripts/download_whole_archive.py \
        --output-dir /media/data/gis_stmk_complete_archive \
        --services Falschfarben_2008_2011 Flug_2013_2015_RGB \
        --max-workers 5

Run without --services to download every service offered by the endpoint.
"""

import argparse
import sys
from pathlib import Path

# Make the package importable when running this file directly from the repo.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.arcgis_rest_downloader import (  # noqa: E402
    get_arcgis_services_to_pd,
    download_raster_tiles_from_service_url,
)

# Default endpoint: GIS Steiermark open orthophotos.
DEFAULT_SERVICE_URL = "https://gis.stmk.gv.at/image/rest/services/OGD_DOP"

# Services available as of May 2025. Pass --services to override.
DEFAULT_SERVICES = [
    "Falschfarben_2008_2011",
    "Falschfarben_2013_2015",
    "Falschfarben_2016_2018",
    "Falschfarben_2019_2021",
    "Falschfarben_2022_2024",
    "Flug_2003_2007_RGB",
    "Flug_2008_2011_RGB",
    "Flug_2013_2015_RGB",
    "Flug_2016_2018_RGB",
    "Flug_2019_2021_RGB",
    "Flug_2022_2024_RGB",
    "SW_1994_2001",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download whole ArcGIS ImageServer services (no bbox).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Base directory. Each service is saved into a subfolder named "
        "after the service (lowercased).",
    )
    parser.add_argument(
        "--service-url",
        default=DEFAULT_SERVICE_URL,
        help="Base URL of the ArcGIS REST service collection.",
    )
    parser.add_argument(
        "--services",
        nargs="*",
        default=None,
        help="Service names to download. Default: the known GIS Steiermark "
        "orthophoto services. Pass 'all' to download every service offered by "
        "the endpoint.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Number of parallel download workers. Keep this modest to stay "
        "friendly to the server.",
    )
    parser.add_argument(
        "--max-retry",
        type=int,
        default=5,
        help="Maximum retries per failed tile request.",
    )
    parser.add_argument(
        "--out-srs",
        type=int,
        default=32633,
        help="Output spatial reference system (EPSG code).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Fetching available services ...")
    services_df = get_arcgis_services_to_pd(args.service_url)
    available = set(services_df["service_name"])

    # Resolve which services to download.
    if args.services and [s.lower() for s in args.services] == ["all"]:
        services = sorted(available)
    elif args.services:
        services = args.services
    else:
        services = DEFAULT_SERVICES

    # Warn about anything the endpoint does not actually offer.
    missing = [s for s in services if s not in available]
    if missing:
        print(f"Warning: these services are not offered by the endpoint: {missing}")
    services = [s for s in services if s in available]

    if not services:
        print("No matching services to download. Available services:")
        for name in sorted(available):
            print(f"  - {name}")
        sys.exit(1)

    print(f"Will download {len(services)} service(s): {services}")

    for service_name in services:
        raw_data_folder = args.output_dir / service_name.lower()
        raw_data_folder.mkdir(parents=True, exist_ok=True)

        print(f"\n=== {service_name} -> {raw_data_folder} ===")
        try:
            download_raster_tiles_from_service_url(
                service_url=args.service_url,
                service_name=service_name,
                output_directory=raw_data_folder,
                bbox_gpkg_path=None,
                max_retry=args.max_retry,
                outSRS=args.out_srs,
                parallel=True,
                max_workers=args.max_workers,
            )
        except Exception as exc:
            # One failing service should not stop the whole archive download.
            print(f"Failed to download service {service_name}: {exc}")

    print("\nAll done.")


if __name__ == "__main__":
    main()
