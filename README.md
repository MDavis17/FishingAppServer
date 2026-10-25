# FishingAppServer

building a range map:
download a csv with lat, long, probability

# start processing env

source fishmaps/bin/activate

# Multiple polygons per band (default 5° clustering)

python3 probability_bands_to_kml.py input.csv output.kml --name "Species" --alpha 0.8

# Tighter clusters → more, smaller polygons

python3 probability_bands_to_kml.py input.csv output.kml --cluster-distance 3

# Looser clusters → fewer, larger polygons

python3 probability_bands_to_kml.py input.csv output.kml --cluster-distance 10

# Single polygon per band (no clustering)

python3 probability_bands_to_kml.py input.csv output.kml --cluster-distance 0

# Different distances per band:

python probability_bands_to_kml.py in.csv out.kml --cluster-distance-low 3 --cluster-distance-mid 5

All bands use 5°:
python probability_bands_to_kml.py in.csv out.kml
or
python probability_bands_to_kml.py in.csv out.kml --cluster-distance 5
Different distances per band:
python probability_bands_to_kml.py in.csv out.kml --cluster-distance-low 3 --cluster-distance-mid 5 --cluster-distance-high 8
Only override one band:
python probability_bands_to_kml.py in.csv out.kml --cluster-distance 5 --cluster-distance-high 10
