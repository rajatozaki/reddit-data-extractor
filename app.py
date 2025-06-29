# app.py - Vercel-ready version

import requests
import json
import csv
import io
import html
from bs4 import BeautifulSoup

from flask import Flask, render_template, request, session, Response, flash, redirect, url_for
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)
# Vercel will need this secret key. For a real app, use an environment variable.
app.secret_key = 'a-super-secret-key-for-vercel'

# --- Helper Functions (No changes needed here) ---

def clean_reddit_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith('/'):
        path = path[:-1]
    if not path.endswith('.json'):
        path += '.json'
    clean_url = urlunparse(('https', parsed_url.netloc, path, '', '', ''))
    return clean_url

def parse_comment(comment_data):
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

def flatten_for_csv(comments, parent_id=None):
    flat_list = []
    for comment in comments:
        soup = BeautifulSoup(comment['body'], 'html.parser')
        plain_text_body = soup.get_text(separator=' ', strip=True)
        flat_list.append({
            'id': comment['id'],
            'parent_id': parent_id,
            'author': comment['author'],
            'score': comment['score'],
            'body': plain_text_body
        })
        if comment['replies']:
            flat_list.extend(flatten_for_csv(comment['replies'], parent_id=comment['id']))
    return flat_list

# --- Flask Routes (Modified to use session) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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
            flash("Failed to parse JSON. The URL might be incorrect.", 'error')
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
        
        # Store data in the session cookie
        session['extracted_data'] = { 'post': post, 'comments': comments }

        return render_template('results.html', post=post, comments=comments)

    # For a GET request, just render the index page
    return render_template('index.html')


# We need to change the route for 'extract' as we combined it into index()
@app.route('/download/<format>')
def download(format):
    # Get data from the session cookie
    data = session.get('extracted_data')
    if not data:
        flash("No data to download. Please extract a thread first.", 'error')
        return redirect(url_for('index'))
    
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
            fieldnames = ['id', 'parent_id', 'author', 'score', 'body']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_comments)
        
        csv_data = '\ufeff' + output.getvalue()
        return Response(
            csv_data.encode('utf-8'),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': f'attachment;filename={filename}_comments.csv'}
        )
    else:
        flash("Invalid download format specified.", 'error')
        return redirect(url_for('index'))
