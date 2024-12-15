import streamlit as st
import pandas as pd
import plotly.express as px

def score_endurance_event(
    distance_km: float,
    elevation_meters: float,
    event_type: str = "run",
    is_draftable: bool = False,
    temperature_c: float = 20.0,
    avg_altitude_m: float = 0.0
) -> float:
    """Calculate normalized grit points for endurance events"""
    DISTANCE_FACTOR = 4.0
    ELEVATION_FACTOR = 6.0
    
    TERRAIN_FACTORS = {
        "run": 1.0,
        "trail_run": 1.4,
        "road_cycle": 1.0,
        "gravel": 1.2,
        "mtb": 1.4
    }
    
    DRAFT_FACTOR = 0.8 if is_draftable else 1.0
    NORMALIZATION_FACTOR = 2.0 / 42.2
    
    # Handle elevation with increased impact (300m = 1 point for running)
    if event_type in ["run", "trail_run"]:
        elevation_score = elevation_meters / 300
        base_score = distance_km * NORMALIZATION_FACTOR + elevation_score
    else:
        distance_km = distance_km / DISTANCE_FACTOR
        elevation_meters = elevation_meters / ELEVATION_FACTOR
        elevation_score = elevation_meters / 300
        base_score = distance_km * NORMALIZATION_FACTOR + elevation_score
    
    # Calculate temperature adjustment - sliding scale
    # Optimal temperature range: 10-20°C
    # Below 10°C: small penalty
    # Above 20°C: increasing difficulty
    if temperature_c <= 10:
        temp_adjustment = (temperature_c - 10) * 0.05  # Small penalty for cold
    elif temperature_c <= 20:
        temp_adjustment = 0  # Optimal range
    else:
        temp_adjustment = (temperature_c - 20) * 0.1  # Gradual increase above 20°C
    
    # Calculate altitude adjustment - sliding scale starting from sea level
    # Progressive difficulty increase with altitude
    if avg_altitude_m < 500:
        altitude_adjustment = (avg_altitude_m / 1000) * 0.8  # Slightly less than 1 point per 1000m
    else:
        altitude_adjustment = 0
    
    # Apply all factors
    terrain_adjusted = base_score * TERRAIN_FACTORS[event_type]
    draft_adjusted = terrain_adjusted * DRAFT_FACTOR
    final_score = draft_adjusted + temp_adjustment + altitude_adjustment
    
    return round(final_score, 2)

# Set page config
st.set_page_config(page_title="Grit Event Scorer", layout="wide")

# Title and description
st.title("Grit Calculator")

# Create two columns for input and results
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Add New Event")
    
    # Event input form
    with st.form("event_form"):
        event_name = st.text_input("Event Name")
        event_type = st.selectbox(
            "Event Type",
            ["run", "trail_run", "road_cycle", "gravel", "mtb"],
            format_func=lambda x: {
                "run": "Road Running",
                "trail_run": "Trail Running",
                "road_cycle": "Road Cycling",
                "gravel": "Gravel Cycling",
                "mtb": "Mountain Biking"
            }[x]
        )
        
        # Basic metrics
        distance = st.number_input("Distance (km)", min_value=0.0, value=42.2)
        elevation = st.number_input("Elevation Gain (meters)", min_value=0.0, value=0.0)
        
        # New inputs for temperature and altitude
        temperature = st.number_input("Average Temperature (°C)", min_value=-20.0, max_value=50.0, value=20.0)
        altitude = st.number_input("Average Altitude (meters)", min_value=0.0, max_value=5000.0, value=0.0)
        
        is_draftable = st.checkbox("Is this a draftable event?")
        
        submitted = st.form_submit_button("Calculate Grit Points")

# Initialize session state for storing events
if 'events' not in st.session_state:
    st.session_state.events = []

# Calculate and store score if form is submitted
if submitted:
    score = score_endurance_event(
        distance,
        elevation,
        event_type,
        is_draftable,
        temperature,
        altitude
    )
    
    new_event = {
        'name': event_name,
        'type': event_type,
        'distance': distance,
        'elevation': elevation,
        'temp': temperature,
        'altitude': altitude,
        'draftable': is_draftable,
        'score': score
    }
    
    st.session_state.events.append(new_event)

# Display results
with col2:
    st.subheader("Event Comparison")
    
    if st.session_state.events:
        # Convert events to DataFrame
        df = pd.DataFrame(st.session_state.events)
        
        # Display formatted table
        st.dataframe(
            df.style.format({
                'distance': '{:.1f}',
                'elevation': '{:.0f}',
                'temp': '{:.1f}',
                'altitude': '{:.0f}',
                'score': '{:.2f}'
            }),
            hide_index=True
        )
        
        # Create bar chart of scores
        fig = px.bar(
            df,
            x='name',
            y='score',
            title='Event Comparison',
            color='type',
            labels={'name': 'Event', 'score': 'Grit Points'}
        )
        st.plotly_chart(fig)
        
        if st.button("Clear All Events"):
            st.session_state.events = []
    else:
        st.info("No events added")

# Add explanation
st.markdown("""
---
### Scoring System:
- Base: Marathon (42.2km) = 2.0 grit points
- Elevation: +1 point per 300m gain
- Temperature adjustments:
  - 10-20°C: Optimal range (no adjustment)
  - Below 10°C: -0.05 points per °C below 10°C
  - Above 20°C: +0.1 points per °C above 20°C
- Altitude: +0.8 points per 1000m above sea level (0 if < 500m)
- Trail/MTB: 1.4x multiplier
- Gravel: 1.2x multiplier
- Drafting: 0.8x multiplier
""")