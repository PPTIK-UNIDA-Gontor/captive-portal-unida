import os

from dotenv import load_dotenv
from pymysql import Error, connect

load_dotenv()

DB_HOST: str = os.getenv("DB_HOST")
DB_PORT: str = os.getenv("DB_PORT")
DB_USERNAME: str = os.getenv("DB_USERNAME")
DB_PASSWORD: str = os.getenv("DB_PASSWORD")
DB_DATABASE: str = os.getenv("DB_DATABASE")

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

        return False


def addUserToRadCheck(username: str, password: str) -> bool:
    """
    Add new user from SSO Callback to Radius Database
    for authentication Purpose
    """

    isUserExist = checkUserInRadCheck(username)

    if isUserExist:
        print("[!] User already exist in Radius Database")
        cursor.close()
        conn.close()
        return True

    transaction = f"INSERT INTO radcheck (username, attribute, op, value) VALUES (%(username)s, 'Cleartext-Password', ':=', %(password)s)"

    print("[+] Adding new user to Radius Database...")

    try:
        cursor.execute(transaction, {"username": username, "password": password})
        print("[+] User added to Radius Database")

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"[-] Error: {e}")

        cursor.close()
        conn.close()
        return False
