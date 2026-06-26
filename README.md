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

#### Orthophoto preset

The `orthophoto` preset downloads the consistent 20 cm, 3-band imagery, both RGB and Falschfarben (CIR), for every campaign from 2008 onward. All of these cover the whole province (~200 x 138 km).

| Service | Years | Type | Resolution | Bands | In preset |
| --- | --- | --- | --- | --- | --- |
| `Falschfarben_2008_2011` | 2008-2011 | CIR | 20 cm | 3 | yes |
| `Flug_2008_2011_RGB` | 2008-2011 | RGB | 20 cm | 3 | yes |
| `Falschfarben_2013_2015` | 2013-2015 | CIR | 20 cm | 3 | yes |
| `Flug_2013_2015_RGB` | 2013-2015 | RGB | 20 cm | 3 | yes |
| `Falschfarben_2016_2018` | 2016-2018 | CIR | 20 cm | 3 | yes |
| `Flug_2016_2018_RGB` | 2016-2018 | RGB | 20 cm | 3 | yes |
| `Falschfarben_2019_2021` | 2019-2021 | CIR | 20 cm | 3 | yes |
| `Flug_2019_2021_RGB` | 2019-2021 | RGB | 20 cm | 3 | yes |
| `Falschfarben_2022_2024` | 2022-2024 | CIR | 20 cm | 3 | yes |
| `Flug_2022_2024_RGB` | 2022-2024 | RGB | 20 cm | 3 | yes |
| `Flug_2003_2007_RGB` | 2003-2007 | RGB | 25 cm | 3 | no (different resolution) |
| `SW_1994_2001` | 1994-2001 | B/W | 50 cm | 1 | no (black & white) |

The two excluded services are still downloadable via `--services` if you need them.

#### DOM preset

For elevation, only `ALS_Hoehen_aktuell_DOM_UTM33N_32633` covers the whole province (its extent matches the orthophotos), so it is the `dom` preset default. The `ALS_Hoehen_2008_2014_*` campaign spans only a ~154 x 95 km sub-area, and the `ALS_Hoehen_2022_2027_*` campaign is still incomplete. To grab a specific campaign or the DGM (terrain) instead, pass it via `--services`.

## ToDo
- Implement processing of DEM data to generate derived products (e.g., slope, aspect).

## Authors
This project was developed by [Daniel Kulmer](https://www.joanneum.at/personen/daniel-kulmer-bsc/) and [Harald Kristen](https://www.linkedin.com/in/harald-kristen/) whilst working on the FFG funded project [Habitalp 2.0](https://projekte.ffg.at/projekt/5123116).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

