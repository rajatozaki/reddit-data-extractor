# Reddit Thread Data Extractor

A simple and powerful web application built with Python and Flask that extracts Reddit thread content, including nested comments and replies, and cleans it for research and analysis. The app transforms raw, messy JSON from Reddit's API into clean, user-friendly formats like structured JSON and CSV.

**Live Demo:** [Link to Live Demo]  
*(Note: Add a link here if you deploy the app on a service like Heroku, PythonAnywhere, or Vercel.)*



## The Problem

Reddit is a goldmine for qualitative data, but accessing it for research can be tedious. While Reddit provides a `.json` endpoint for any thread, the raw data is deeply nested and contains raw HTML, encoded characters, and other noise. This makes it difficult to use directly for analysis in tools like Excel, Pandas, or other research software.

This project was built to solve that problem by providing a one-click solution to get clean, structured data from any Reddit thread.

## Features

-   **Simple Web Interface:** Just paste a Reddit thread URL and click "Extract."
-   **Hierarchical Data Parsing:** Accurately reconstructs the nested comment-reply structure.
-   **Data Cleaning:** Strips all HTML tags from comments and decodes special HTML entities, providing plain text content.
-   **Multiple Export Formats:** Download the extracted data as:
    -   **Structured JSON:** Contains the main post and all comments in a nested hierarchy.
    -   **Clean CSV:** A flattened, table-like format of all comments, perfect for spreadsheets and data analysis tools.
-   **Robust & Scalable:** Handles large threads by using a server-side caching mechanism to overcome browser cookie size limitations.
-   **UTF-8 Compliant CSV:** Generates CSV files with a Byte Order Mark (BOM) to ensure correct character rendering (including emojis and non-English characters) in Microsoft Excel.

## Tech Stack

-   **Backend:** Python, Flask
-   **Frontend:** HTML, CSS
-   **Data Processing:** Requests (for API calls), BeautifulSoup4 (for HTML parsing)
-   **Version Control:** Git & GitHub

## Key Challenges & Solutions

This project involved solving several common web development and data processing challenges:

1.  **State Management for Large Payloads:**
    -   **Problem:** Storing extracted data in the Flask session (which uses client-side cookies) failed for large threads due to the 4KB cookie size limit.
    -   **Solution:** I implemented a server-side caching strategy. The large data payload is saved as a temporary JSON file on the server, and only a small, unique file ID is stored in the user's session. This makes the app scalable to threads of any size.

2.  **Data Sanitization and Cleaning:**
    -   **Problem:** The Reddit API returns comment bodies as raw HTML (`<p>`, `<blockquote>`, etc.) with encoded characters (e.g., `'`). This is unusable for analysis.
    -   **Solution:** I created a data cleaning pipeline using the **BeautifulSoup** library to parse the HTML, strip all tags, and convert HTML entities into their plain text equivalents.

3.  **CSV Character Encoding:**
    -   **Problem:** Special characters (like `’` or `€`) appeared as gibberish (e.g., `â€™`) when the CSV was opened in Microsoft Excel.
    -   **Solution:** I resolved this by prepending a UTF-8 **Byte Order Mark (BOM)** to the CSV output. This acts as a universal signal for spreadsheet programs to correctly interpret the file's encoding.

## How to Run Locally

To run this project on your own machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YourUsername/reddit-data-extractor.git
    cd reddit-data-extractor
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate
    
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You will need to create a `requirements.txt` file. You can generate one with the command `pip freeze > requirements.txt`)*

4.  **Run the Flask application:**
    ```bash
    flask run
    ```

5.  Open your web browser and navigate to `http://127.0.0.1:5000`.

---
