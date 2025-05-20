# ArcGIS REST Downloader

A Python package for downloading original raster tiles from ArcGIS ImageServer REST services for a region of interest, without size limitations.
This gives users full control over the pre-processing and merging of the original raster tiles. Download data for any region of interest, limited only by your local RAM for processing.

This package features:
- Query available services from ArcGIS REST endpoints.
- Download raster tiles that intersect with a specified bounding box.
- Create Cloud Optimized GeoTIFFs (COGs) from downloaded & merged tiles.

This repository is configured to work with the ArcGIS ImageServer REST API from [GIS Steiermark](https://gis.stmk.gv.at). You can also explore the [different ways of accessing](https://gis.stmk.gv.at/image/rest/services/OGD_DOP) their open raster and vector data.

# TODO
- Implement processing of DEM data to generate derived products (e.g., slope, aspect).

## Usage
Check out the `example-usage-rest-downloader.ipynb` notebook in the `notebooks/` directory for a demonstration.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.