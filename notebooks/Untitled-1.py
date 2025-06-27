{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Exploratory Data Analysis of NBER Papers\n",
    "\n",
    "This notebook performs an initial exploratory data analysis (EDA) on the NBER working papers dataset stored in our SQLite database. The goal is to understand the basic characteristics of the data, such as:\n",
    "\n",
    "- The distribution of papers over time.\n",
    "- The typical length of paper abstracts.\n",
    "- The most common words found in the abstracts."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import sqlite3\n",
    "from pathlib import Path\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from sklearn.feature_extraction.text import CountVectorizer\n",
    "\n",
    "# Set plot style\n",
    "sns.set_theme(style=\"whitegrid\")\n",
    "plt.rcParams['figure.figsize'] = (12, 6)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Load Data from SQLite Database"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Define paths - assuming the notebook is in the 'notebooks' directory\n",
    "PROJECT_ROOT = Path().resolve().parent\n",
    "DB_PATH = PROJECT_ROOT / \"data\" / \"03_primary\" / \"nber_papers.db\"\n",
    "TABLE_NAME = \"papers\"\n",
    "\n",
    "# Connect to the database and load data\n",
    "try:\n",
    "    conn = sqlite3.connect(DB_PATH)\n",
    "    df = pd.read_sql(f\"SELECT * FROM {TABLE_NAME}\", conn)\n",
    "    conn.close()\n",
    "    print(f\"Successfully loaded {len(df)} records.\")\n",
    "except Exception as e:\n",
    "    print(f\"Error loading data: {e}\")\n",
    "\n",
    "# Display basic info and the first few rows\n",
    "df.info()\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Distribution of Papers Over Time"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Convert issue_date to datetime and extract the year\n",
    "df['issue_date'] = pd.to_datetime(df['issue_date'])\n",
    "df['year'] = df['issue_date'].dt.year\n",
    "\n",
    "# Plot the number of papers published per year\n",
    "plt.figure(figsize=(15, 7))\n",
    "papers_per_year = df['year'].value_counts().sort_index()\n",
    "sns.lineplot(x=papers_per_year.index, y=papers_per_year.values)\n",
    "plt.title('Number of NBER Working Papers Published Per Year', fontsize=16)\n",
    "plt.xlabel('Year')\n",
    "plt.ylabel('Number of Papers')\n",
    "plt.xlim(papers_per_year.index.min(), papers_per_year.index.max())\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Text Analysis: Abstract Length\n",
    "\n",
    "Let's analyze the length of the abstracts to understand their general verbosity."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Calculate the number of words in each abstract\n",
    "# Fill NaN values with an empty string first\n",
    "df['abstract_word_count'] = df['abstract'].fillna('').apply(lambda x: len(x.split()))\n",
    "\n",
    "# Plot the distribution of abstract word counts\n",
    "plt.figure(figsize=(12, 6))\n",
    "sns.histplot(df['abstract_word_count'], bins=50, kde=True)\n",
    "plt.title('Distribution of Abstract Word Count', fontsize=16)\n",
    "plt.xlabel('Number of Words')\n",
    "plt.ylabel('Frequency')\n",
    "plt.xlim(0, df['abstract_word_count'].quantile(0.99)) # Exclude extreme outliers for better visualization\n",
    "plt.show()\n",
    "\n",
    "print(df['abstract_word_count'].describe())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. Text Analysis: Most Common Words\n",
    "\n",
    "Finally, let's identify the most frequently used words in the paper abstracts. We will use `CountVectorizer` and remove common English stop words to get meaningful results."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Use CountVectorizer to get word counts\n",
    "# We limit to the top 1000 features and remove English stop words\n",
    "vectorizer = CountVectorizer(max_features=1000, stop_words='english')\n",
    "X = vectorizer.fit_transform(df['abstract'].fillna(''))\n",
    "\n",
    "# Sum the word counts across all documents\n",
    "word_counts = pd.DataFrame({\n",
    "    'word': vectorizer.get_feature_names_out(),\n",
    "    'count': X.toarray().sum(axis=0)\n",
    "})\n",
    "\n",
    "# Get the top 20 most common words\n",
    "top_words = word_counts.sort_values(by='count', ascending=False).head(20)\n",
    "\n",
    "# Plot the top 20 words\n",
    "plt.figure(figsize=(12, 8))\n",
    "sns.barplot(x='count', y='word', data=top_words, palette='viridis')\n",
    "plt.title('Top 20 Most Common Words in NBER Abstracts', fontsize=16)\n",
    "plt.xlabel('Frequency Count')\n",
    "plt.ylabel('Word')\n",
    "plt.show()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.x"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
