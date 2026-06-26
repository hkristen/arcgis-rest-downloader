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

`download_raster_tiles_from_service_url` and `download_and_create_cog` accept `parallel=True` to download tiles concurrently, and `max_workers=N` (default 10) to set the worker count. Keep `max_workers` modest (e.g. 5) to stay friendly to the server.

### Download the whole archive

To download entire services (e.g. all of Styria), use `scripts/download_whole_archive.py`. It fetches the original tiles plus metadata in parallel, without creating COGs. Two presets pick the endpoint and a default service list (`--help` lists all options):

```bash
# Orthophotos (RGB + CIR) for the whole province
python scripts/download_whole_archive.py --preset orthophoto --output-dir /media/data/orthophotos

# Provincewide digital surface model (DOM)
python scripts/download_whole_archive.py --preset dom --output-dir /media/data/dom
```

Override the defaults with `--services NAME ...` (or `--services all`) to pick specific services.

#### Orthophoto preset

Consistent 20 cm, 3-band imagery (RGB + Falschfarben/CIR) for every campaign from 2008 onward, all covering the whole province (~200 x 138 km):

| Service | Years | Type | Resolution | In preset |
| --- | --- | --- | --- | --- |
| `Falschfarben_2008_2011` / `Flug_2008_2011_RGB` | 2008-2011 | CIR / RGB | 20 cm | yes |
| `Falschfarben_2013_2015` / `Flug_2013_2015_RGB` | 2013-2015 | CIR / RGB | 20 cm | yes |
| `Falschfarben_2016_2018` / `Flug_2016_2018_RGB` | 2016-2018 | CIR / RGB | 20 cm | yes |
| `Falschfarben_2019_2021` / `Flug_2019_2021_RGB` | 2019-2021 | CIR / RGB | 20 cm | yes |
| `Falschfarben_2022_2024` / `Flug_2022_2024_RGB` | 2022-2024 | CIR / RGB | 20 cm | yes |
| `Flug_2003_2007_RGB` | 2003-2007 | RGB | 25 cm | no (different resolution) |
| `SW_1994_2001` | 1994-2001 | B/W | 50 cm | no (black & white) |

The excluded services are still reachable via `--services`.

#### DOM preset

Only `ALS_Hoehen_aktuell_DOM_UTM33N_32633` covers the whole province, so it is the `dom` default. The `ALS_Hoehen_2008_2014_*` campaign spans only ~154 x 95 km and `ALS_Hoehen_2022_2027_*` is still incomplete. Use `--services` for a specific campaign or the DGM (terrain).

## ToDo
- Implement processing of DEM data to generate derived products (e.g., slope, aspect).

## Authors
This project was developed by [Daniel Kulmer](https://www.joanneum.at/personen/daniel-kulmer-bsc/) and [Harald Kristen](https://www.linkedin.com/in/harald-kristen/) whilst working on the FFG funded project [Habitalp 2.0](https://projekte.ffg.at/projekt/5123116).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

