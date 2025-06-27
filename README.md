# 📈 NBER Research Trends Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://nber-methods-etl.streamlit.app/)

An interactive dashboard to explore the frequency of key terms, methods, and topics mentioned in National Bureau of Economic Research (NBER) working papers over time. This project is inspired by *The Economist's* "Dedicated followers of fashion" chart, which tracks the popularity of various economic methodologies.



![There is a figure produced by [The Economist](https://www.economist.com/finance-and-economics/2016/11/24/economists-are-prone-to-fads-and-the-latest-is-machine-learning) about the latest fad in the discipline being machine learning.](assets/methods.png)


---

## About The Project

This application provides a real-time, interactive tool for researchers, students, and enthusiasts to track the evolving landscape of economic research. Users can visualize trends for suggested terms or input their own custom queries to see how their prevalence has changed over the decades.

The project is built with an automated data pipeline that ensures the data is always up-to-date with the latest NBER publications.

### Key Features

- **Interactive Time-Series Chart:** Visualize the frequency of multiple terms on a single chart.
- **Custom Search:** Enter any term or phrase to generate a new trend line on the fly.
- **Adjustable Smoothing:** Use a slider to apply a moving average (from 0 to 10 years) to smooth out trend lines.
- **Dynamic Zoom:** The chart automatically adjusts its x-axis to focus on the most active period for the selected terms.
- **Recent Papers Tab:** See a list of all papers published in the last 7 days.
- **Detailed Data Tables:** View and link to the specific papers that are included in any chart you generate.

---

## Automated Data Pipeline

The data for this application is kept current via a fully automated pipeline powered by **GitHub Actions**.

1.  **Scheduled Execution:** A workflow is scheduled to run every week (Sunday at 3:15 AM UTC). It can also be triggered manually.
2.  **Data Ingestion:** The runner executes `pipeline/01_ingest_data.py`, which downloads the latest metadata from the NBER's public data repository. It compares these papers against the existing `nber_papers.db` SQLite database and appends only the new entries.
3.  **Data Processing:** The runner then executes `pipeline/02_process_text.py`. This script reads from the updated SQLite database, cleans and prepares the text data, and generates the final `nber_full_text.parquet` file that the Streamlit app uses.
4.  **Commit & Push:** The action checks if the database or Parquet file has changed. If changes are detected, it automatically commits the updated files back to this repository with the message "Automated data update".

This ensures that the deployed Streamlit app (`app/app.py`)always has access to the most recent data without any manual intervention.

---

## Running the Project Locally

To run this project on your local machine, follow these steps:

**Prerequisites:**
- Python 3.9+
- `uv` (or `pip`) package installer

**Setup:**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/j-jayes/NBER-methods-etl.git](https://github.com/j-jayes/NBER-methods-etl.git)
    cd NBER-methods-etl
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    This project uses separate requirements files for the pipeline and the app. Install the app dependencies to run it locally.
    ```bash
    pip install uv
    uv pip sync requirements.txt
    ```

4.  **Run the data pipeline (first time only):**
    The first time you run the project, you must build the data files. Install the pipeline requirements and run the scripts.
    ```bash
    uv pip sync requirements-pipeline.txt
    python pipeline/01_ingest_data.py
    python pipeline/02_process_text.py
    ```

5.  **Run the Streamlit app:**
    ```bash
    streamlit run app/app.py
    ```

    The application should now be open in your web browser.