def get_current_weather(location: str) -> str:
    """Retrieves the current weather status for a specified city or location."""
    # A simple mock utility to demonstrate contextual execution inputs
    loc_lower = location.lower()
    if "delhi" in loc_lower or "noida" in loc_lower:
        return "Weather Status: 28°C, Heavy continuous rainfall, Overcast skies, 92% Humidity."
    return f"Weather Status: 22°C, Partially cloudy for {location}, 60% Humidity."