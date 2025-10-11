import os
from uuid import uuid4

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session

from db_connection import addUserToRadCheck, checkUserInRadCheck
from flask_session import Session

# Load env file
load_dotenv()

FLASK_SECRET = os.getenv("FLASK_SECRET_KEY", uuid4())

SSO_CLIENT_ID = os.getenv("SSO_CLIENT_ID", "sso_client_id")
SSO_CLIENT_SECRET = os.getenv("SSO_CLIENT_SECRET", "sso_client_secret")
SSO_BASE_URL = os.getenv("SSO_BASE_URL", "https://your_sso_domain.com")
SSO_REDIRECT_URI = os.getenv(
    "SSO_REDIRECT_URI", "https://your_domain.com/auth/callback"
)

# App init
app = Flask(__name__)
app.secret_key = FLASK_SECRET

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/auth/redirect", methods=["POST"])
def redirect_login():
    macAddress = request.form.get("mac")
    ipAddress = request.form.get("ip")
    loginLinkOnly = request.form.get("link-login-only")
    error = request.form.get("error")
    username = request.form.get("username")
    isLoggedIn = True if request.form.get("logged-in") == "yes" else False

    session["mac"] = macAddress
    session["ip"] = ipAddress
    session["link-login-only"] = loginLinkOnly
    session["error"] = error
    session["username"] = username
    session["logged-in"] = isLoggedIn

    return redirect("/auth/login")


@app.route("/auth/login", methods=["GET"])
def login():
    # Check username udah login atau belum
    isUserLoggedIn = session.get("logged-in", False)

    isUserAvailable = checkUserInRadCheck(str(session.get("username")))

    if isUserLoggedIn and isUserAvailable:
        return render_template("success.html", username=str(session.get("username")))

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

            # Klo link login only nya kosong, berarti hotspot nya belum di setting
            if (
                not session.get("link-login-only")
                or session.get("link-login-only") == ""
            ):
                return render_template("error.html", message="Hotspot Belum Di Setting")

            return render_template(
                "connect.html",
                username=username,
                password=uniqueId,
                destination="https://unida.gontor.ac.id",
                linkLoginOnly=session.get("link-login-only"),
            )
        else:
            return render_template(
                "error.html", message="Gagal menambahkan user ke Radius Database"
            )

    except requests.exceptions.RequestException as e:
        return render_template("error.html", message=f"User Gagal Diperoleh: {e}")


# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
