import socket

from pyrad.client import Client, Timeout
from pyrad.packet import AccessRequest


def authenticateUser(username: str, token: str, serverIp: str, secret: str):
    try:
        # Radius CLIENT
        client = Client(server=serverIp, secret=secret.encode("utf-8"), dict=None)

        req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
        req["User-Password"] = req.PwCrypt(token)

        print(f"Sending Radius Request to {serverIp}...")
        response = client.SendPacket(req)

        if response.code == 2:
            print("Authentication Success")

            sessionTimeout = response.get("Session-Timeout", [None])[0]
            return True, sessionTimeout
        else:
            print("Authentication Failed")
            return False, None

    except Timeout as err_timeout:
        print(f"ERROR: Radius Server timeout.\n{err_timeout}")
        return False, None
    except socket.error as err_socket:
        print(f"ERROR: Failed to connect to Radius Server.\n{err_socket}")
        return False, None
