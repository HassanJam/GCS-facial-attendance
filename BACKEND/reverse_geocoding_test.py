import time
from geopy.geocoders import Nominatim

def reverse_geocode(lat, lon, retries=3, delay=2):
    """
    Reverse geocodes latitude and longitude into an address with retry mechanism.
    
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        retries (int): Number of retry attempts.
        delay (int): Delay between retries in seconds.
        
    Returns:
        str: Address corresponding to the latitude and longitude or error message.
    """
    try:
        # Initialize geolocator
        geolocator = Nominatim(user_agent="reverse_geocoder")
        
        # Perform reverse geocoding with retries
        for attempt in range(retries):
            try:
                # Perform reverse geocoding with a timeout of 5 seconds
                location = geolocator.reverse((lat, lon), language="en", timeout=5)
                return location.address if location else "Address not found"
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    return f"An error occurred: {e}"

    except Exception as e:
        return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    latitude = 31.5092109
    longitude = 74.3369365
    address = reverse_geocode(latitude, longitude)
    print(f"The address for coordinates ({latitude}, {longitude}) is:\n{address}")
