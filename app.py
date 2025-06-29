import requests
import json
import csv
import io
import html
import os
import uuid
from bs4 import BeautifulSoup # <-- ADDED: For parsing HTML

from flask import Flask, render_template, request, session, Response, flash, redirect, url_for
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-dev'

TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_data')
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# --- Helper Functions ---

# clean_reddit_url and parse_comment functions remain the same...

def clean_reddit_url(url):
    """Sanitizes the Reddit URL to ensure it points to the .json endpoint."""
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith('/'):
        path = path[:-1]
    if not path.endswith('.json'):
        path += '.json'
    clean_url = urlunparse(('https', parsed_url.netloc, path, '', '', ''))
    return clean_url

def parse_comment(comment_data):
    """Recursively parses a comment and its replies."""
    if comment_data['kind'] != 't1':
        return None
    data = comment_data['data']
    comment = {
        'id': data.get('id'),
        'author': data.get('author', '[deleted]'),
        'body': html.unescape(data.get('body_html', '')),
        'score': data.get('score', 0),
        'replies': []
    }
    if 'replies' in data and data['replies'] and 'data' in data['replies']:
        for reply_data in data['replies']['data']['children']:
            parsed_reply = parse_comment(reply_data)
            if parsed_reply:
                comment['replies'].append(parsed_reply)
    return comment


# --- THIS FUNCTION IS UPDATED ---
def flatten_for_csv(comments, parent_id=None):
    """
    Flattens the nested comment structure for CSV export
    and cleans the HTML from the comment body.
    """
    flat_list = []
    for comment in comments:
        # Use BeautifulSoup to parse the HTML body and extract plain text
        soup = BeautifulSoup(comment['body'], 'html.parser')
        plain_text_body = soup.get_text(separator=' ', strip=True)

        flat_list.append({
            'id': comment['id'],
            'parent_id': parent_id,
            'author': comment['author'],
            'score': comment['score'],
            'body': plain_text_body # <-- Use the cleaned text
        })
        if comment['replies']:
            flat_list.extend(flatten_for_csv(comment['replies'], parent_id=comment['id']))
    return flat_list


# --- Flask Routes ---

# index and extract routes remain the same...
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url = request.form.get('url')
    if not url:
        flash('Please provide a Reddit URL.', 'error')
        return redirect(url_for('index'))
    json_url = clean_reddit_url(url)
    headers = {'User-Agent': 'My Reddit Extractor 1.0'}
    try:
        response = requests.get(json_url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching data from Reddit: {e}", 'error')
        return redirect(url_for('index'))
    except json.JSONDecodeError:
        flash("Failed to parse JSON. The URL might be incorrect or the response was not valid JSON.", 'error')
        return redirect(url_for('index'))

    post_data = data[0]['data']['children'][0]['data']
    post = {
        'title': post_data.get('title'),
        'author': post_data.get('author'),
        'selftext': html.unescape(post_data.get('selftext_html', '')),
        'score': post_data.get('score'),
        'url': f"https://www.reddit.com{post_data.get('permalink')}"
    }
    comments_data = data[1]['data']['children']
    comments = []
    for comment_data in comments_data:
        parsed_comment = parse_comment(comment_data)
        if parsed_comment:
            comments.append(parsed_comment)
    
    extracted_data = {'post': post, 'comments': comments}
    data_id = str(uuid.uuid4())
    filepath = os.path.join(TEMP_FOLDER, f"{data_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
    session['data_id'] = data_id

    return render_template('results.html', post=post, comments=comments)


# --- THIS FUNCTION IS UPDATED ---
@app.route('/download/<format>')
def download(format):
    """Handles downloading the data as JSON or CSV."""
    data_id = session.get('data_id')
    if not data_id:
        flash("No data to download. Please extract a thread first.", 'error')
        return redirect(url_for('index'))
    
    filepath = os.path.join(TEMP_FOLDER, f"{data_id}.json")

    if not os.path.exists(filepath):
        flash("Error: Temporary data file not found. Please try extracting again.", 'error')
        return redirect(url_for('index'))

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    post_title = data['post']['title'].replace(' ', '_').replace('/', '')[:30]
    filename = f"reddit_{post_title}"

    if format == 'json':
        return Response(
            json.dumps(data, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename={filename}.json'}
        )
    elif format == 'csv':
        flat_comments = flatten_for_csv(data['comments'])
        output = io.StringIO()
        if not flat_comments:
            output.write("No comments found.")
        else:
            # We will now only include the columns you requested, plus id/parent_id
            fieldnames = ['id', 'parent_id', 'author', 'score', 'body']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_comments)
        
        # --- KEY CHANGE FOR EXCEL COMPATIBILITY ---
        # 1. Prepend a BOM (Byte Order Mark) to the CSV data.
        #    This is a special signal that tells Excel the file is UTF-8.
        csv_data = '\ufeff' + output.getvalue()

        # 2. Encode the string to bytes and specify the charset in the mimetype.
        return Response(
            csv_data.encode('utf-8'),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment;filename={filename}_comments.csv'}
        )
    else:
        flash("Invalid download format specified.", 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)