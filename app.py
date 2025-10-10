import os
from uuid import uuid4

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session

from db_connection import addUserToRadCheck

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


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/auth/redirect", methods=["POST"])
def redirect_login():
    macAddress = request.form["mac"]
    ipAddress = request.form["ip"]
    loginLinkOnly = request.form["link-login-only"]
    error = request.form["error"]

    session["mac"] = macAddress
    session["ip"] = ipAddress
    session["link-login-only"] = loginLinkOnly
    session["error"] = error

    return redirect("/auth/login")


@app.route("/auth/login", methods=["GET"])
def login():
    authUrl = f"{SSO_BASE_URL}/oauth/login?client_id={SSO_CLIENT_ID}&redirect_uri={SSO_REDIRECT_URI}&response_type=code&scope=read write&state={uuid4()}"
    return redirect(authUrl)


@app.route("/auth/callback")
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
        token: str = tokenData["access_token"]
    except requests.exceptions.RequestException as e:
        return render_template("error.html", message=f"Token Gagal Diperoleh: {e}")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        userResponse = requests.get(f"{SSO_BASE_URL}/oauth/userinfo", headers=headers)
        userResponse.raise_for_status()
        userData = userResponse.json()

        username: str = userData["name"]
        fullname: str = f"{userData["given_name"]} {userData["family_name"]}"
        email: str = userData["email"]
        uniqueId: str = userData["idnumber"]  # Ntar ini yang di jadiin Password

        if not username or not fullname or not email or not uniqueId:
            return render_template("error.html", message="User Data Tidak Valid")

        isAddedToRadCheck: bool = addUserToRadCheck(username, uniqueId)

        if isAddedToRadCheck:
            return render_template(
                "connect.html",
                username=username,
                password=uniqueId,
                destination="https://unida.gontor.ac.id",
                linkLoginOnly=(
                    session["link-login-only"]
                    if session.get("link-login-only")
                    else f"{RADIUS_SERVER}/login"
                ),
            )
        else:
            return render_template(
                "error.html", message="Gagal menambahkan user ke Radius Database"
            )

    except requests.exceptions.RequestException as e:
        return render_template("error.html", message=f"User Gagal Diperoleh: {e}")


# Run app
if __name__ == "__main__":
    app.run(host="10.10.17.100", port=5000, debug=True)
