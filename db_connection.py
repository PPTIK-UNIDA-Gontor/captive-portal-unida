import os

from dotenv import load_dotenv
from pymysql import Error, connect

load_dotenv()

DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT: str | int = os.getenv("DB_PORT", 3306)
DB_USERNAME: str = os.getenv("DB_USERNAME", "radius")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "radius")
DB_DATABASE: str = os.getenv("DB_DATABASE", "radius")

conn = connect(
    host=DB_HOST,
    port=int(DB_PORT),
    user=DB_USERNAME,
    password=DB_PASSWORD,
    database=DB_DATABASE,
)

cursor = conn.cursor()


def checkUserInRadCheck(username: str) -> bool:
    transaction = f"SELECT username FROM radcheck WHERE username = %(username)s"

    try:
        cursor.execute(transaction, {"username": username})
        user = cursor.fetchone()

        if not user:
            print("[!] User not found in Radius Database")
            return False

        print("[+] User found in Radius Database")

        return True
    except Error as e:
        print(f"[-] Error: {e}")

        cursor.close()
        conn.close()
        return False


def addUserToRadCheck(username: str, password: str) -> bool:
    """
    Add new user from SSO Callback to Radius Database
    for authentication Purpose
    """

    isUserExist = checkUserInRadCheck(username)

    if isUserExist:
        print("[!] User already exist in Radius Database")
        return True

    transaction = f"INSERT INTO radcheck (username, attribute, op, value) VALUES (%(username)s, 'Cleartext-Password', ':=', %(password)s)"

    print("[+] Adding new user to Radius Database...")

    try:
        cursor.execute(transaction, {"username": username, "password": password})
        print("[+] User added to Radius Database")

        conn.commit()
        return True
    except Error as e:
        print(f"[-] Error: {e}")

        cursor.close()
        conn.close()
        return False
