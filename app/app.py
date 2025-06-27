import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(
    page_title="NBER Research Trends",
    page_icon="📈",
    layout="wide"
)

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "03_primary" / "nber_full_text.parquet"

# --- Caching & Data Loading ---

@st.cache_data
def load_data(path):
    """Loads the full-text data with caching."""
    if not path.exists():
        st.error(f"Data file not found at {path}. Please run the data pipeline first.")
        return None
    try:
        df = pd.read_parquet(path)
        df['total_papers_in_year'] = df.groupby('year')['paper'].transform('count')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_data
def calculate_frequencies(_df, terms):
    """Calculates the frequency of a list of terms in the dataframe."""
    if _df is None or not terms:
        return pd.DataFrame()

    results = []
    for term in terms:
        if not term.strip():
            continue
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        contains_term = _df['full_text'].str.contains(pattern, regex=True)
        term_counts = _df[contains_term].groupby('year')['paper'].count()
        total_papers = _df.groupby('year')['total_papers_in_year'].first()
        frequency_by_year = (term_counts / total_papers * 100).fillna(0)
        term_df = frequency_by_year.reset_index()
        term_df.columns = ['year', 'frequency']
        term_df['term'] = term
        results.append(term_df)

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()


def plot_trends(df, ma_window, smart_xaxis):
    """Generates the interactive plot."""
    if df is None or df.empty:
        return None

    plot_df = df.sort_values(by=['term', 'year'])
    
    if ma_window > 0:
        plot_df['plot_frequency'] = plot_df.groupby('term')['frequency'].transform(lambda x: x.rolling(window=ma_window, min_periods=1).mean())
        plot_title = f"Mentions in NBER Papers (% of total, {ma_window}-year moving average)"
    else:
        plot_df['plot_frequency'] = plot_df['frequency']
        plot_title = "Mentions in NBER Papers (% of total)"
    
    xaxis_range = None
    if smart_xaxis:
        threshold = 0.05
        active_years = plot_df[plot_df['plot_frequency'] > threshold]
        if not active_years.empty:
            first_active_year = active_years['year'].min()
            start_year = first_active_year - 10
            min_data_year = plot_df['year'].min()
            final_start_year = max(start_year, min_data_year)
            xaxis_range = [final_start_year, plot_df['year'].max()]

    fig = px.line(plot_df, x='year', y='plot_frequency', color='term', title=plot_title,
                  labels={'year': 'Year', 'plot_frequency': '% of Papers', 'term': 'Search Term'},
                  template="plotly_white")
    if xaxis_range:
        fig.update_xaxes(range=xaxis_range)
    fig.update_layout(legend_title_text='', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_traces(hovertemplate='<b>%{data.name}</b><br>Year: %{x}<br>Frequency: %{y:.2f}%<extra></extra>')
    return fig

# --- Main Application ---
st.title("📈 Dedicated Followers of Fashion")
st.markdown("An interactive dashboard to explore trends in NBER working papers.")

full_text_df = load_data(DATA_PATH)

if full_text_df is not None:
    # --- Sidebar for User Controls ---
    with st.sidebar:
        st.header("⚙️ Controls")
        
        suggested_terms = ["Difference-in-differences", "Regression discontinuity", "Randomised controlled trial", "Machine learning", "Big data", "Artificial intelligence", "Dynamic stochastic general equilibrium"]
        selected_suggested_terms = st.multiselect("Select suggested terms:", options=suggested_terms, default=["Difference-in-differences", "Machine learning"])
        custom_terms_input = st.text_area("Enter custom terms (one per line):", placeholder="e.g., climate change\nmonetary policy")
        
        st.markdown("---")
        st.subheader("Chart Options")
        ma_window = st.slider("Moving average window (years):", min_value=0, max_value=10, value=3, help="Set to 0 to disable.")
        smart_zoom = st.checkbox("Zoom to active period", value=True)
        
        st.markdown("---")
        st.markdown("**Data Source:** [NBER](https://www.nber.org/research/data/nber-working-papers-and-chapters-metadata)")
        if DATA_PATH.exists():
            last_updated = pd.Timestamp(DATA_PATH.stat().st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')
            st.info(f"Data last updated:\n{last_updated}")

    # --- Main Panel with Tabs ---
    tab1, tab2 = st.tabs(["Trends Dashboard", "Newly Added Papers"])

    with tab1:
        custom_terms = [term.strip() for term in custom_terms_input.split('\n') if term.strip()]
        all_selected_terms = list(dict.fromkeys(selected_suggested_terms + custom_terms))

        if not all_selected_terms:
            st.warning("Please select or enter at least one term to display the chart.")
        else:
            trends_df = calculate_frequencies(full_text_df, tuple(all_selected_terms))
            trends_fig = plot_trends(trends_df, ma_window, smart_zoom)
            if trends_fig:
                st.plotly_chart(trends_fig, use_container_width=True)

            # --- Data Table for Papers in Chart ---
            st.subheader("Papers Mentioning Selected Terms")
            with st.spinner("Filtering papers..."):
                search_pattern = r'|'.join([r'\b' + re.escape(term.lower()) + r'\b' for term in all_selected_terms])
                papers_in_chart_df = full_text_df[full_text_df['full_text'].str.contains(search_pattern, regex=True)].copy()
                
                # Create the URL column
                papers_in_chart_df['paper_url'] = "https://www.nber.org/papers/" + papers_in_chart_df['paper']
                
                st.dataframe(
                    papers_in_chart_df,
                    column_config={
                        "issue_date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                        "title": "Title",
                        "author": "Authors",
                        "paper_url": st.column_config.LinkColumn(
                            "Paper Link",
                            display_text="Read Paper"
                        ),
                        # Hide unnecessary columns
                        "paper": None, "year": None, "doi": None, "full_text": None, "total_papers_in_year": None
                    },
                    hide_index=True,
                    use_container_width=True
                )
    
    with tab2:
        st.subheader("Papers Added in the Last 7 Days")
        
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_papers = full_text_df[full_text_df['issue_date'] >= seven_days_ago].copy()
        recent_papers.sort_values(by='issue_date', ascending=False, inplace=True)
        
        if recent_papers.empty:
            st.info("No new papers have been added in the last 7 days.")
        else:
            # Create the URL column
            recent_papers['paper_url'] = "https://www.nber.org/papers/" + recent_papers['paper']
            
            st.dataframe(
                recent_papers,
                column_config={
                    "issue_date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                    "title": "Title",
                    "author": "Authors",
                    "paper_url": st.column_config.LinkColumn(
                        "Paper Link", 
                        display_text="Read Paper"
                    ),
                    # Hide unnecessary columns
                    "paper": None, "year": None, "doi": None, "full_text": None, "total_papers_in_year": None
                },
                hide_index=True,
                use_container_width=True
            )
