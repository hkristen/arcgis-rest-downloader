"""Download whole GIS Steiermark archives (all tiles, no bbox), in parallel.

This wrapper downloads every tile of one or more ArcGIS ImageServer services to
a local directory, in parallel. It is meant for grabbing a complete archive
(e.g. all of Styria) rather than a single region of interest.

No COGs are created: the script only fetches the original tiles plus their
metadata, so you keep full control over any later merging / processing.

Two presets are built in (select with --preset):
  - orthophoto : RGB and Falschfarben (CIR) imagery from the OGD_DOP endpoint.
  - dom        : the provincewide surface model (DOM) from the OGD_Hoehen
                 endpoint.

Examples:
    # All orthophoto services (RGB + CIR) for the whole province
    python scripts/download_whole_archive.py --preset orthophoto \
        --output-dir /media/data/gis_stmk_orthophotos

    # The provincewide DOM
    python scripts/download_whole_archive.py --preset dom \
        --output-dir /media/data/gis_stmk_dom --max-workers 5

    # A specific selection of services
    python scripts/download_whole_archive.py --preset dom \
        --services ALS_Hoehen_2008_2014_DOM_50cm_UTM33N_32633 \
        --output-dir /media/data/gis_stmk_dom_2008
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

# Built-in presets: endpoint URL + sensible default service list.
PRESETS = {
    # RGB and Falschfarben (CIR) orthophotos at a consistent 20 cm resolution,
    # 3 bands each, provincewide. The older B/W (SW_1994_2001, 50 cm, 1 band)
    # and Flug_2003_2007_RGB (25 cm) are deliberately excluded; pass them via
    # --services if you want them. Services available as of May 2025.
    "orthophoto": {
        "service_url": "https://gis.stmk.gv.at/image/rest/services/OGD_DOP",
        "services": [
            "Falschfarben_2008_2011",
            "Flug_2008_2011_RGB",
            "Falschfarben_2013_2015",
            "Flug_2013_2015_RGB",
            "Falschfarben_2016_2018",
            "Flug_2016_2018_RGB",
            "Falschfarben_2019_2021",
            "Flug_2019_2021_RGB",
            "Falschfarben_2022_2024",
            "Flug_2022_2024_RGB",
        ],
    },
    # Digital surface model (DOM). Of the DOM services on the OGD_Hoehen
    # endpoint, only "aktuell" covers the whole province (its extent matches
    # the orthophotos). The 2008_2014 campaign spans only a ~154x95 km
    # sub-area and the 2022_2027 campaign is still incomplete, so neither is a
    # provincewide default. Pass --services to grab a specific campaign.
    "dom": {
        "service_url": "https://gis.stmk.gv.at/image/rest/services/OGD_Hoehen",
        "services": [
            "ALS_Hoehen_aktuell_DOM_UTM33N_32633",
        ],
    },
}


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
        "--preset",
        choices=sorted(PRESETS),
        default="orthophoto",
        help="Which built-in endpoint + default service list to use.",
    )
    parser.add_argument(
        "--service-url",
        default=None,
        help="Override the preset's ArcGIS REST endpoint URL.",
    )
    parser.add_argument(
        "--services",
        nargs="*",
        default=None,
        help="Service names to download. Default: the preset's service list. "
        "Pass 'all' to download every service offered by the endpoint.",
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

    preset = PRESETS[args.preset]
    service_url = args.service_url or preset["service_url"]

    print(f"Endpoint: {service_url}")
    print("Fetching available services ...")
    services_df = get_arcgis_services_to_pd(service_url)
    available = set(services_df["service_name"])

    # Resolve which services to download.
    if args.services and [s.lower() for s in args.services] == ["all"]:
        services = sorted(available)
    elif args.services:
        services = args.services
    else:
        services = preset["services"]

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
                service_url=service_url,
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
