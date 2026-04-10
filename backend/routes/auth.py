from flask import Blueprint, request, jsonify
from config import get_db

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/auth", methods=["POST"])
def auth():
    try:
        data = request.get_json()

        print("Incoming Data:", data)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username and password required"
            })

        db = get_db()
        cur = db.cursor()

        #  CREATE TABLE (VERY IMPORTANT)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)
        db.commit()

        #  CHECK USER
        user = cur.execute(
            "SELECT username, password FROM users WHERE username=?",
            (username,)
        ).fetchone()

        print("User Found:", user)

        #  LOGIN
        if user:
            if user[1] == password:
                return jsonify({
                    "success": True,
                    "message": "Login successful"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Wrong password"
                })

        #  REGISTER (AUTO)
        cur.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, password)
        )
        db.commit()

        return jsonify({
            "success": True,
            "message": "User registered"
        })

    except Exception as e:
        print("Auth Error:", e)
        return jsonify({
            "success": False,
            "error": str(e)  # 👈 shows real error
        }), 500