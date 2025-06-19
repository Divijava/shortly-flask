from flask import Flask, request, redirect, render_template
import string, random
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import qrcode
import io
import base64

app = Flask(__name__)

# Render PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shortly_db_4mdg_user:T1QBJODWO5pydNnm344wLqgy37IuQzj2@dpg-d19jc1je5dus7392sq60-a.oregon-postgres.render.com/shortly_db_4mdg")

# Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Generate short ID
def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def home():
    short_url = None
    qr_b64 = None  # Needed for GET request
    if request.method == 'POST':
        original_url = request.form['url']
        short_id = generate_short_id()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO urls (short_id, original_url, created_at) VALUES (%s, %s, NOW())", (short_id, original_url))
        conn.commit()
        cur.close()
        conn.close()

        short_url = request.host_url + short_id

        # Generate QR code
        img = qrcode.make(short_url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

    # Get 5 recent shortened links
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT short_id, original_url, created_at FROM urls ORDER BY created_at DESC LIMIT 5")
    links = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', short_url=short_url, links=links, qr_b64=qr_b64)

@app.route('/<short_id>')
def redirect_to_original(short_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT original_url FROM urls WHERE short_id = %s", (short_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return redirect(result['original_url'])
    else:
        return 'Invalid short URL', 404

if __name__ == '__main__':
    app.run(debug=True)
