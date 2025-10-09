import os
from uuid import uuid4

import requests
from dotenv import load_dotenv
from flask import (Flask, json, redirect, render_template, request, session,
                   url_for)

# Load env file
load_dotenv()

FLASK_SECRET = os.getenv("FLASK_SECRET_KEY")

SSO_CLIENT_ID = os.getenv("SSO_CLIENT_ID")
SSO_CLIENT_SECRET = os.getenv("SSO_CLIENT_SECRET")
SSO_BASE_URL = os.getenv("SSO_BASE_URL")
SSO_REDIRECT_URI = os.getenv("SSO_REDIRECT_URI")

RADIUS_SERVER = os.getenv("RADIUS_SERVER")
RADIUS_SECRET = os.getenv("RADIUS_SECRET")


# App init
app = Flask(__name__)
app.secret_key = FLASK_SECRET


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/auth/login")
def login():
    authUrl = f"{SSO_BASE_URL}/oauth/login?client_id={SSO_CLIENT_ID}&redirect_uri={SSO_REDIRECT_URI}&response_type=code&scope=read write&state={uuid4()}"
    return redirect(authUrl)


def callback():
    # Auth Code dari SSO Callback
    authCode = request.args.get("code")

    if not authCode:
        return render_template("error.html", message="Auth Code Tidak Ditemukan")

    tokenPayload = {
        "client_id": SSO_CLIENT_ID,
        "client_secret": SSO_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": authCode,
        "redirect_uri": SSO_REDIRECT_URI,
    }

    try:
        tokenResponse = requests.post(f"{SSO_BASE_URL}/oauth/token", data=tokenPayload)
        tokenResponse.raise_for_status()

        tokenData = tokenResponse.json()
        token = tokenData["access_token"]

        return json.jsonify(token)
    except Exception as e:
        raise e


# Run app
if __name__ == "__main__":
    app.run(host="103.195.19.121", port=5000, debug=True)
