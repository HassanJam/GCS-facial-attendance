from geopy.geocoders import Nominatim

def reverse_geocode(lat, lon):
    """
    Reverse geocodes latitude and longitude into an address.
    
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        
    Returns:
        str: Address corresponding to the latitude and longitude.
    """
    try:
        # Initialize geolocator
        geolocator = Nominatim(user_agent="reverse_geocoder")
        
        # Perform reverse geocoding
        location = geolocator.reverse((lat, lon), language="en")
        
        # Return the address
        return location.address if location else "Address not found"
    except Exception as e:
        return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    latitude = 31.5092109
    longitude = 74.3369365
    address = reverse_geocode(latitude, longitude)
