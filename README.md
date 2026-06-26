# ArcGIS REST Downloader

A Python tool for downloading original raster tiles from ArcGIS ImageServer REST services for a region of interest, without size limitations.
This gives users full control over the pre-processing and merging of the original raster tiles. Download data for any region of interest, limited only by your local RAM for processing.

This tool features:
- Query available services from ArcGIS REST endpoints.
- Download raster tiles that intersect with a specified bounding box.
- Download whole services (the complete archive) when no bounding box is given.
- Optional parallel downloading for much faster transfers on large areas.
- Create Cloud Optimized GeoTIFFs (COGs) from downloaded & merged tiles.

This repository is configured to work with the ArcGIS ImageServer REST API from [GIS Steiermark](https://gis.stmk.gv.at). You can also explore the [different ways of accessing](https://www.landesentwicklung.steiermark.at/cms/beitrag/12866797/145230171/) their open raster and vector data.

## Usage

Clone the repository to your local machine and check out the `example-usage-rest-downloader.ipynb` notebook in the `notebooks/` directory.

### Parallel downloading

`download_raster_tiles_from_service_url` and `download_and_create_cog` accept two extra arguments:

- `parallel=True` gathers tile metadata and downloads tiles concurrently.
- `max_workers=N` sets the number of concurrent workers (default 10).

```python
from src.arcgis_rest_downloader import download_raster_tiles_from_service_url

download_raster_tiles_from_service_url(
    service_url="https://gis.stmk.gv.at/image/rest/services/OGD_DOP",
    service_name="Falschfarben_2008_2011",
    output_directory="data/raw/falschfarben_2008_2011",
    bbox_gpkg_path="data/my_region.gpkg",  # or None to download the whole service
    parallel=True,
    max_workers=8,
)
```

Keep `max_workers` modest (e.g. 5) to stay friendly to the server.

### Download the whole archive

To download entire services (e.g. the complete orthophoto archive for all of Styria), use the wrapper script in `scripts/`. It downloads the original tiles plus their metadata, without creating COGs, so you keep full control over any later merging:

```bash
# A selection of services into per-service subfolders
python scripts/download_whole_archive.py \
    --output-dir /media/data/gis_stmk_complete_archive \
    --services Falschfarben_2008_2011 Flug_2013_2015_RGB \
    --max-workers 5

# Every service offered by the endpoint
python scripts/download_whole_archive.py \
    --output-dir /media/data/gis_stmk_complete_archive \
    --services all
```

Run `python scripts/download_whole_archive.py --help` for all options. Omitting `--services` downloads the known GIS Steiermark orthophoto services.

Note: this script and its default service list cover only the RGB and Falschfarben (CIR) orthophoto imagery (`OGD_DOP` endpoint). Elevation data (DOM/DGM from the `OGD_Hoehen` endpoint) is not included here.

## ToDo
- Implement processing of DEM data to generate derived products (e.g., slope, aspect).

## Authors
This project was developed by [Daniel Kulmer](https://www.joanneum.at/personen/daniel-kulmer-bsc/) and [Harald Kristen](https://www.linkedin.com/in/harald-kristen/) whilst working on the FFG funded project [Habitalp 2.0](https://projekte.ffg.at/projekt/5123116).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

