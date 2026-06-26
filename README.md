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

To download entire services (e.g. the complete archive for all of Styria), use the wrapper script in `scripts/`. It downloads the original tiles plus their metadata, without creating COGs, so you keep full control over any later merging. Two built-in presets select the endpoint and a sensible default service list:

- `--preset orthophoto` (default): RGB and Falschfarben (CIR) imagery from the `OGD_DOP` endpoint.
- `--preset dom`: the provincewide digital surface model (DOM) from the `OGD_Hoehen` endpoint.

```bash
# All orthophoto services (RGB + CIR) for the whole province
python scripts/download_whole_archive.py --preset orthophoto \
    --output-dir /media/data/gis_stmk_orthophotos --max-workers 5

# The provincewide DOM
python scripts/download_whole_archive.py --preset dom \
    --output-dir /media/data/gis_stmk_dom --max-workers 5

# A specific selection of services
python scripts/download_whole_archive.py --preset orthophoto \
    --services Falschfarben_2008_2011 Flug_2013_2015_RGB \
    --output-dir /media/data/gis_stmk_orthophotos

# Every service offered by the endpoint
python scripts/download_whole_archive.py --preset dom --services all \
    --output-dir /media/data/gis_stmk_hoehen
```

Run `python scripts/download_whole_archive.py --help` for all options.

Notes on coverage:
- The `orthophoto` preset covers only the RGB and Falschfarben (CIR) imagery (`OGD_DOP` endpoint).
- For elevation, only `ALS_Hoehen_aktuell_DOM_UTM33N_32633` covers the whole province (its extent matches the orthophotos), so it is the `dom` preset default. The `ALS_Hoehen_2008_2014_*` campaign spans only a ~154x95 km sub-area, and the `ALS_Hoehen_2022_2027_*` campaign is still incomplete. To grab a specific campaign or the DGM (terrain) instead, pass it via `--services`.

## ToDo
- Implement processing of DEM data to generate derived products (e.g., slope, aspect).

## Authors
This project was developed by [Daniel Kulmer](https://www.joanneum.at/personen/daniel-kulmer-bsc/) and [Harald Kristen](https://www.linkedin.com/in/harald-kristen/) whilst working on the FFG funded project [Habitalp 2.0](https://projekte.ffg.at/projekt/5123116).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

