import googlemaps
from datetime import datetime
from math import radians, cos, sin, sqrt, atan2
from dotenv import load_dotenv
import os

from playground.actions_manager import agent_action

load_dotenv()

# Initialize the Google Maps client
api_key = os.getenv("GOOGLE_API_KEY")
gmaps = googlemaps.Client(key=api_key)

gmaps = googlemaps.Client(key=api_key)


@agent_action
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two latitude/longitude points using the Haversine formula.

    Parameters:
    lat1 (float): Latitude of the first point.
    lon1 (float): Longitude of the first point.
    lat2 (float): Latitude of the second point.
    lon2 (float): Longitude of the second point.

    Returns:
    float: Distance between the two points in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


@agent_action
def get_direction_stops(origin_name, destination_name, min_distance_km):
    """
    Get a list of waypoints between the origin and destination, with each waypoint
    being at least a specified minimum distance from the previous one.

    Parameters:
    origin_name (str): The starting location name.
    destination_name (str): The ending location name.
    min_distance_km (float): The minimum distance between waypoints in kilometers.

    Returns:
    list: A list of tuples representing the latitude and longitude of each waypoint.
    """
    # Get directions from origin to destination
    directions_result = gmaps.directions(
        origin_name, destination_name, mode="driving", departure_time=datetime.now()
    )

    # Extract waypoints (lat, long) based on minimum distance
    waypoints = []
    last_waypoint = None

    for leg in directions_result[0]["legs"]:
        # omit the first 3 steps
        legs = leg["steps"]
        for step in legs[3:]:
            end_location = step["end_location"]
            if last_waypoint:
                distance = haversine(
                    last_waypoint[0],
                    last_waypoint[1],
                    end_location["lat"],
                    end_location["lng"],
                )
                if distance >= min_distance_km:
                    waypoints.append((end_location["lat"], end_location["lng"]))
                    last_waypoint = (end_location["lat"], end_location["lng"])
            else:
                waypoints.append((end_location["lat"], end_location["lng"]))
                last_waypoint = (end_location["lat"], end_location["lng"])

    return waypoints


@agent_action
def get_places(lat, long, place_type="restaurant", num_results=10):
    """
    Get a list of places near the specified latitude and longitude.

    Parameters:
    lat (float): The latitude of the location.
    long (float): The longitude of the location.
    place_type (str): The type of places to search for (e.g., "restaurant", "tourist_attraction").
    num_results (int): The number of results to return.

    Returns:
    dict: A dictionary containing the name of the waypoint and lists of places.
    """
    # Reverse geocode to get the name of the location
    reverse_geocode_result = gmaps.reverse_geocode((lat, long))
    location_name = (
        reverse_geocode_result[0]["formatted_address"]
        if reverse_geocode_result
        else "Unknown location"
    )

    # Search for places near the given coordinates
    places_result = gmaps.places_nearby(
        location=(lat, long), radius=5000, type=place_type
    )

    places_details = []

    for place in places_result["results"][:num_results]:
        place_id = place["place_id"]
        place_detail = gmaps.place(place_id=place_id)

        name = place_detail["result"].get("name")
        rating = place_detail["result"].get("rating")
        price_level = place_detail["result"].get("price_level", "N/A")
        distance = place.get("distance", "N/A")
        hours = (
            place_detail["result"].get("opening_hours", {}).get("weekday_text", "N/A")
        )
        reviews = place_detail["result"].get("reviews", [])
        top_reviews = [review["text"] for review in reviews[:10]]

        place_info = {
            "name": name,
            "rating": rating,
            "price_level": price_level,
            "distance": distance,
            "hours": hours,
            "top_reviews": top_reviews,
        }

        places_details.append(place_info)

    return {"location_name": location_name, "places": places_details}


@agent_action
def get_trip_highlights(origin, destination, min_distance_km):
    """
    Get a list of waypoints between the origin and destination, with highlights
    of the top 10 restaurants and top 10 tourist attractions at each waypoint.

    Parameters:
    origin (str): The starting location name.
    destination (str): The ending location name.
    min_distance_km (float): The minimum distance between waypoints in kilometers.

    Returns:
    list: A list of dictionaries, each containing the waypoint name, coordinates,
          top restaurants, and top tourist attractions.
    """
    # Get waypoints along the route
    waypoints = get_direction_stops(origin, destination, min_distance_km)

    highlights = []
    for waypoint in waypoints:
        lat, long = waypoint
        restaurants = get_places(lat, long, place_type="restaurant", num_results=10)
        attractions = get_places(
            lat, long, place_type="tourist_attraction", num_results=10
        )

        highlight = {
            "waypoint": {
                "lat": lat,
                "long": long,
                "name": restaurants["location_name"],
            },
            "restaurants": restaurants["places"],
            "attractions": attractions["places"],
        }

        highlights.append(highlight)

    return highlights


# # Example usage
# origin = "Calgary, AB"
# destination = "White Rock, BC"
# min_distance_km = 50  # Minimum distance between waypoints in kilometers
# trip_highlights = get_trip_highlights(origin, destination, min_distance_km)
# for highlight in trip_highlights:
#     print(f"Waypoint: {highlight['waypoint']}")
#     print("Top Restaurants:")
#     for restaurant in highlight["restaurants"]:
#         print(
#             f" - {restaurant['name']} (Rating: {restaurant['rating']}, Price Level: {restaurant['price_level']})"
#         )
#     print("Top Attractions:")
#     for attraction in highlight["attractions"]:
#         print(f" - {attraction['name']} (Rating: {attraction['rating']})")
