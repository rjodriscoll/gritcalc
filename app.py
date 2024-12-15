import streamlit as st
import pandas as pd
import plotly.express as px

def score_endurance_event(
    distance_km: float,
    elevation_meters: float,
    event_type: str = "run",
    roughness: float = 0.0,
    draft_percentage: float = 0.0,
    temperature_c: float = 20.0,
    avg_altitude_m: float = 0.0
) -> float:
    """Calculate normalized grit points for endurance events"""
    # Check minimum distances
    MIN_RUN_DISTANCE = 21.2  # Half marathon
    MIN_CYCLE_DISTANCE = 70.0
    
    if (event_type in ["run", "trail_run"] and distance_km < MIN_RUN_DISTANCE) or \
       (event_type in ["road_cycle", "gravel", "mtb"] and distance_km < MIN_CYCLE_DISTANCE):
        return 0.0
    
    DISTANCE_FACTOR = 3.0
    ELEVATION_FACTOR = 4.0
    
    terrain_factor = 1 + roughness
    
    # Calculate draft factor based on percentage (0% = 1.0, 100% = 0.7)
    DRAFT_FACTOR = 1.0 - (draft_percentage / 100 * 0.3)
    
    NORMALIZATION_FACTOR = 2.0 / 42.2

    if event_type in ["run", "trail_run"]:
        elevation_score = elevation_meters / 400
        base_score = distance_km * NORMALIZATION_FACTOR + elevation_score
    else:
        distance_km = distance_km / DISTANCE_FACTOR
        elevation_meters = elevation_meters / ELEVATION_FACTOR
        elevation_score = elevation_meters / 400
        base_score = distance_km * NORMALIZATION_FACTOR + elevation_score
    
    # Temperature adjustment
    if temperature_c <= 10:
        temp_adjustment = (temperature_c - 10) * 0.05
    elif temperature_c <= 20:
        temp_adjustment = 0
    else:
        temp_adjustment = (temperature_c - 20) * 0.1
    
    # Altitude adjustment
    if avg_altitude_m < 500:
        altitude_adjustment = (avg_altitude_m / 1000) * 0.8
    else:
        altitude_adjustment = 0
    
    # Apply all factors
    terrain_adjusted = base_score * terrain_factor
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
        
        # Roughness slider
        roughness = st.slider(
            "Terrain Roughness (0 = smooth, 1 = extreme chonk)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="0 = road/track, 1.0 = extreme technical terrain"
        )
        
        # New draft percentage slider
        draft_percentage = st.slider(
            "Drafting Percentage",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            help="0% = solo riding, 100% = full draft benefit"
        )
        
        # Temperature and altitude
        temperature = st.number_input("Average Temperature (°C)", min_value=-20.0, max_value=50.0, value=20.0)
        altitude = st.number_input("Average Altitude (meters)", min_value=0.0, max_value=5000.0, value=0.0)
        
        submitted = st.form_submit_button("Calculate Grit Points")

# Initialize session state
if 'events' not in st.session_state:
    st.session_state.events = []

# Calculate and store score if form is submitted
if submitted:
    score = score_endurance_event(
        distance,
        elevation,
        event_type,
        roughness,
        draft_percentage,
        temperature,
        altitude
    )
    
    new_event = {
        'name': event_name,
        'type': event_type,
        'distance': distance,
        'elevation': elevation,
        'roughness': roughness,
        'draft_pct': draft_percentage,
        'temp': temperature,
        'altitude': altitude,
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
                'roughness': '{:.1f}',
                'draft_pct': '{:.0f}',
                'temp': '{:.1f}',
                'altitude': '{:.0f}',
                'score': '{:.2f}'
            }),
            hide_index=True
        )
        
        # Create bar chart
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
- Minimum distances required:
  - Running events: 21.2km (half marathon)
  - Cycling events: 80km
  - Events below these distances score 0 points
- Base: Marathon (42.2km) = 2.0 grit points
- Distance: 3:1 ratio running:cycling
- Elevation: +1 point per 400m gain with a 4:1 running:cycling ratio
- Terrain Roughness: 0-1 scale e.g.
  - 0.0 = smooth surface (1x multiplier)
  - 1.0 = 100% off road, extreme technical terrain (2x multiplier)
- Drafting: 0-100% scale
  - 0% = solo effort (1.0x multiplier)
  - 100% = full draft benefit (0.7x multiplier)
- Temperature adjustments:
  - 10-20°C: Optimal range (no adjustment)
  - Below 10°C: -0.05 points per °C below 10°C
  - Above 20°C: +0.1 points per °C above 20°C
- Altitude: +0.8 points per 1000m above sea level (0 if < 500m)
""")