from flask import Blueprint, request, jsonify
from config import get_db

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/auth", methods=["POST"])
def auth():
    try:
        data = request.json

        # DEBUG (helps you see request in terminal)
        print("Incoming Data:", data)

        username = data.get("username")
        password = data.get("password")

        # Validation
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username and password required"
            })

        db = get_db()
        cur = db.cursor()

        # Check if user exists
        user = cur.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        print("User Found:", user)

        # LOGIN CASE
        if user:
            if user["password"] == password:
                return jsonify({
                    "success": True,
                    "login": True,
                    "message": "Login successful"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Wrong password"
                })

        # REGISTER CASE
        cur.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, password)
        )
        db.commit()

        return jsonify({
            "success": True,
            "registered": True,
            "message": "User registered successfully"
        })

    except Exception as e:
        print("Auth Error:", e)
        return jsonify({
            "success": False,
            "error": "Server error"
        })