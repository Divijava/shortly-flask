from flask import Flask, request, redirect, render_template
import string
import random
import psycopg2
import os
import urllib.parse as up

app = Flask(__name__)

# Connect to PostgreSQL using DATABASE_URL (for Render)
def get_db_connection():
    up.uses_netloc.append("postgres")
    url = up.urlparse(os.environ["DATABASE_URL"])
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

# Generate short ID
def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def home():
    short_url = None
    if request.method == 'POST':
        original_url = request.form['url']
        short_id = generate_short_id()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO urls (short_id, original_url) VALUES (%s, %s)", (short_id, original_url))
        conn.commit()
        cur.close()
        conn.close()

        short_url = request.host_url + short_id

    return render_template('index.html', short_url=short_url)

@app.route('/<short_id>')
def redirect_to_original(short_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT original_url FROM urls WHERE short_id = %s", (short_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return redirect(result[0])
    else:
        return 'Invalid short URL', 404

if __name__ == '__main__':
    app.run(debug=True)
