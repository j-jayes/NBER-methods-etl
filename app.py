import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- Configuration ---
# Set page configuration - this must be the first Streamlit command
st.set_page_config(
    page_title="NBER Research Trends",
    page_icon="📈",
    layout="wide"
)

# Define paths
# This assumes the app.py file is in the 'app' directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "03_primary" / "nber_trends.parquet"

# --- Helper Functions ---

@st.cache_data
def load_data(path):
    """
    Loads the processed data from a Parquet file with caching.
    """
    if not path.exists():
        st.error(f"Data file not found at {path}. Please run the data pipeline first.")
        return None
    try:
        df = pd.read_parquet(path)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def plot_trends(df, selected_terms, use_moving_average):
    """
    Generates an interactive plot of term frequencies over time.
    """
    if df is None or df.empty:
        return None

    # Filter data for selected terms
    plot_df = df[df['term'].isin(selected_terms)]

    # Calculate moving average if the option is selected
    if use_moving_average:
        plot_df = plot_df.sort_values(by=['term', 'year'])
        plot_df['frequency'] = plot_df.groupby('term')['frequency'].transform(lambda x: x.rolling(window=5, min_periods=1).mean())
        plot_title = "Mentions in NBER Abstracts (% of total papers, 5-year moving average)"
    else:
        plot_title = "Mentions in NBER Abstracts (% of total papers)"

    # Create the plot
    fig = px.line(
        plot_df,
        x='year',
        y='frequency',
        color='term',
        title=plot_title,
        labels={
            'year': 'Year',
            'frequency': '% of Papers',
            'term': 'Search Term'
        },
        template="plotly_white"
    )
    
    # Customize the plot appearance
    fig.update_layout(
        legend_title_text='',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Year: %{x}<br>Frequency: %{y:.2f}%<extra></extra>', customdata=plot_df[['term']])

    return fig

# --- Main Application ---

# Load the data
trends_df = load_data(DATA_PATH)

# Title and introduction
st.title("📈 Dedicated Followers of Fashion")
st.markdown("""
This dashboard visualizes the frequency of key terms and methods mentioned in the titles and abstracts
of NBER working papers over time, inspired by a chart from *The Economist*.
""")

if trends_df is not None:
    # --- Sidebar for User Controls ---
    with st.sidebar:
        st.header("⚙️ Controls")

        # Get the list of all available terms from the data
        all_terms = trends_df['term'].unique().tolist()
        
        # Multi-select for terms
        selected_terms = st.multiselect(
            "Select terms to display:",
            options=all_terms,
            default=all_terms[:4] # Default to the first 4 terms
        )

        # Checkbox for moving average
        use_ma = st.checkbox(
            "Use 5-year moving average",
            value=True
        )

        # Data source and last update info
        st.markdown("---")
        st.markdown("**Data Source:** [NBER](https://www.nber.org/research/data/nber-working-papers-and-chapters-metadata)")
        if DATA_PATH.exists():
            last_updated = pd.Timestamp(DATA_PATH.stat().st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')
            st.info(f"Data last updated:\n{last_updated}")

    # --- Main Panel for Chart ---
    if not selected_terms:
        st.warning("Please select at least one term from the sidebar to display the chart.")
    else:
        # Generate and display the plot
        trends_fig = plot_trends(trends_df, selected_terms, use_ma)
        if trends_fig:
            st.plotly_chart(trends_fig, use_container_width=True)

