from django.shortcuts import render
import requests

from .models import Location

# Create your views here.
def fetch_coordinates(apikey, address):
    try:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']\
            ['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

        Location.objects.create(
            address=address,
            lon=lon,
            lat=lat
        )
        return lat, lon
    except requests.HTTPError:
        return None