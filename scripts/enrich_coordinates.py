"""Enrich dados_apartamentos.csv with per-row latitude/longitude based on Bairro.

Geocodes each unique neighborhood once via Nominatim, then applies a small
random jitter per row so listings in the same neighborhood don't all
collapse onto the exact same point on a map.
"""
import random
import time

import pandas as pd
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim

SOURCE_PATH = "data/dados_apartamentos.csv"
OUTPUT_PATH = "data/dados_apartamentos_with_coordinates.csv"

# Roughly +-500m jitter (1 degree of latitude ~= 111km).
JITTER_DEGREES = 0.0045

random.seed(42)

df = pd.read_csv(SOURCE_PATH, sep=";")

unique_neighborhoods = df["Bairro"].unique()
geolocator = Nominatim(user_agent="rio_rentals_geocoder")

neighborhood_coordinates = {}
print(f"Found {len(unique_neighborhoods)} unique neighborhoods. Starting geocoding...")

for neighborhood in unique_neighborhoods:
    query = f"{neighborhood}, Rio de Janeiro, RJ, Brazil"
    try:
        location = geolocator.geocode(query, timeout=10)
        if location:
            neighborhood_coordinates[neighborhood] = (location.latitude, location.longitude)
            print(f"Success: {neighborhood} -> {location.latitude}, {location.longitude}")
        else:
            neighborhood_coordinates[neighborhood] = (None, None)
            print(f"Not found: {neighborhood}")
    except GeocoderTimedOut:
        neighborhood_coordinates[neighborhood] = (None, None)
        print(f"Timeout error for: {neighborhood}")

    time.sleep(1.1)


def jittered_coordinate(neighborhood, axis):
    lat, lon = neighborhood_coordinates.get(neighborhood, (None, None))
    if lat is None or lon is None:
        return None
    base = lat if axis == "lat" else lon
    return base + random.uniform(-JITTER_DEGREES, JITTER_DEGREES)


df["Latitude"] = df["Bairro"].apply(lambda b: jittered_coordinate(b, "lat"))
df["Longitude"] = df["Bairro"].apply(lambda b: jittered_coordinate(b, "lon"))

df.to_csv(OUTPUT_PATH, sep=";", index=False)

missing = df["Latitude"].isna().sum()
print(f"\nProcessing complete! Data saved to {OUTPUT_PATH}")
print(f"Rows without coordinates: {missing}")
