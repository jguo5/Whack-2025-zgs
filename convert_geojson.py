import geopandas as gpd

# Path to your shapefile (update if it's somewhere else)
shapefile_path = r"C:\Users\iwuba\Downloads\WHACK2025\Whack-2025-zgs\cb_2018_us_county_5m.shp"

# Read shapefile, restore SHX if missing
gdf = gpd.read_file(shapefile_path, SHAPE_RESTORE_SHX=True)

# Save as GeoJSON in the same folder
geojson_path = shapefile_path.replace(".shp", ".geojson")
gdf.to_file(geojson_path, driver="GeoJSON")

print(f"GeoJSON saved at: {geojson_path}")
