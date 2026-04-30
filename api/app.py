from app import app as application

# Vercel's Python builder will use this WSGI app.
# If you want to run locally: `python api/app.py`
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))