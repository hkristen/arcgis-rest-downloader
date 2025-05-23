# ArcGIS REST Downloader

A Python tool for downloading original raster tiles from ArcGIS ImageServer REST services for a region of interest, without size limitations.
This gives users full control over the pre-processing and merging of the original raster tiles. Download data for any region of interest, limited only by your local RAM for processing.

This tool features:
- Query available services from ArcGIS REST endpoints.
- Download raster tiles that intersect with a specified bounding box.
- Create Cloud Optimized GeoTIFFs (COGs) from downloaded & merged tiles.

This repository is configured to work with the ArcGIS ImageServer REST API from [GIS Steiermark](https://gis.stmk.gv.at). You can also explore the [different ways of accessing](https://www.landesentwicklung.steiermark.at/cms/beitrag/12866797/145230171/) their open raster and vector data.

## Usage

Clone the repository to cour local machine and check out the `example-usage-rest-downloader.ipynb` notebook in the `notebooks/` directory.

## ToDo
- Implement processing of DEM data to generate derived products (e.g., slope, aspect).

## Authors
This project was developed by [Daniel Kulmer](https://www.joanneum.at/personen/daniel-kulmer-bsc/) and [Harald Kristen](https://www.linkedin.com/in/harald-kristen/) whilst working on the FFG funded project [Habitalp 2.0](https://projekte.ffg.at/projekt/5123116).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

