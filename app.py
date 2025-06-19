from flask import Flask, request, redirect, render_template
import string, random
import psycopg2
import qrcode
import io
import base64

app = Flask(__name__)

# PostgreSQL connection (update with your credentials or use Render env vars)
def get_db_connection():
    return psycopg2.connect(
        host="localhost",  # or your Render hostname
        database="shortly_db",
        user="postgres",
        password="yourpassword"
    )

# Generate short id
def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def home():
    short_url = None
    qr_b64 = None

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        original_url = request.form['url']
        short_id = generate_short_id()
        short_url = request.host_url + short_id

        cur.execute("INSERT INTO urls (short_id, original_url) VALUES (%s, %s)", (short_id, original_url))
        conn.commit()

        # Generate QR code
        qr = qrcode.make(short_url)
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Get all links
    cur.execute("SELECT original_url, short_id FROM urls ORDER BY created_at DESC LIMIT 10")
    links = [(row[0], request.host_url + row[1]) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template('index.html', short_url=short_url, qr_b64=qr_b64, links=links)

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
