import os
import random
import string
import hashlib
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Blueprint, request, jsonify
from config import get_db, init_tables

auth_routes = Blueprint("auth", __name__)

SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

_reset_store: dict = {}   # { email: {code, expires_at} }


# ─── helpers ────────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _gen_code(k: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=k))


def _log(db, user_id, username: str, action: str, ip: str = ""):
    try:
        db.execute(
            "INSERT INTO login_activity(user_id,username,action,ip) VALUES(?,?,?,?)",
            (user_id, username, action, ip)
        )
    except Exception as exc:
        print(f"[Auth] Activity log error: {exc}")


def _send_code_email(to: str, code: str) -> bool:
    """Send reset code via Gmail SMTP. Falls back to console if not configured."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[Auth] [DEV] Reset code for {to}: {code}")
        return True
    try:
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = "VoiceAI — Your Password Reset Code"
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to
        html = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:auto;
                    background:#07090f;color:#e8ecf4;padding:48px 40px;border-radius:20px;
                    border:1px solid rgba(80,140,255,.15);">
          <h2 style="margin:0 0 6px;font-size:24px;font-weight:800;">VoiceAI</h2>
          <p style="color:#6b7a99;margin:0 0 30px;">Password Reset Request</p>
          <p style="margin:0 0 22px;line-height:1.7;">
            Use the code below to reset your password.
            It expires in <strong style="color:#e8ecf4;">10 minutes</strong>.
          </p>
          <div style="background:#0d1220;border:1px solid rgba(80,140,255,.25);
                      border-radius:14px;padding:32px;text-align:center;margin-bottom:28px;">
            <span style="font-size:42px;font-weight:900;letter-spacing:14px;
                         color:#3a7fff;font-family:'Courier New',monospace;">{code}</span>
          </div>
          <p style="color:#555f70;font-size:13px;">
            If you did not request this, ignore this email — your account is safe.
          </p>
        </div>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(SMTP_EMAIL, SMTP_PASSWORD)
            srv.sendmail(SMTP_EMAIL, to, msg.as_string())
        return True
    except Exception as exc:
        print(f"[Auth] Email send error: {exc}")
        return False


# ─── routes ─────────────────────────────────────────────────────────────────

@auth_routes.route("/auth", methods=["POST"])
def auth():
    try:
        init_tables()
        data     = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")
        ip       = request.remote_addr or ""

        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required."})

        db  = get_db()
        cur = db.cursor()
        row = cur.execute(
            "SELECT id, username, name, password FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not row:
            db.close()
            return jsonify({"success": False,
                            "error": "No account found with that username. Please register first."})

        stored  = row["password"]
        matched = (stored == _hash(password)) or (stored == password)

        if not matched:
            _log(db, row["id"], username, "failed_login", ip)
            db.commit()
            db.close()
            return jsonify({"success": False,
                            "error": "Incorrect password. Please check and try again."})

        # Upgrade plain-text password to hash silently
        if stored == password:
            db.execute("UPDATE users SET password = ? WHERE id = ?", (_hash(password), row["id"]))

        db.execute("UPDATE users SET last_login = ? WHERE id = ?",
                   (datetime.datetime.now().isoformat(), row["id"]))
        _log(db, row["id"], username, "login", ip)
        db.commit()
        db.close()

        return jsonify({"success": True, "username": row["username"], "name": row["name"]})

    except Exception as exc:
        print(f"[Auth] /auth error: {exc}")
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500


@auth_routes.route("/register", methods=["POST"])
def register():
    try:
        init_tables()
        data     = request.get_json(silent=True) or {}
        name     = data.get("name", "").strip()
        email    = data.get("email", "").strip().lower()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        ip       = request.remote_addr or ""

        if not all([name, email, username, password]):
            return jsonify({"success": False, "error": "All fields are required."})
        if "@" not in email or "." not in email.split("@")[-1]:
            return jsonify({"success": False, "error": "Please enter a valid email address."})
        if len(password) < 6:
            return jsonify({"success": False,
                            "error": "Password must be at least 6 characters long."})
        if len(username) < 3:
            return jsonify({"success": False,
                            "error": "Username must be at least 3 characters long."})
        if not username.replace("_", "").replace(".", "").isalnum():
            return jsonify({"success": False,
                            "error": "Username may only contain letters, numbers, dots and underscores."})

        db  = get_db()
        cur = db.cursor()

        if cur.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            db.close()
            return jsonify({"success": False,
                            "error": "That username is already taken. Please choose another."})
        if cur.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            db.close()
            return jsonify({"success": False,
                            "error": "An account with that email already exists."})

        db.execute(
            "INSERT INTO users(name, username, password, email) VALUES(?,?,?,?)",
            (name, username, _hash(password), email)
        )
        db.commit()
        uid = cur.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()["id"]
        _log(db, uid, username, "register", ip)
        db.commit()
        db.close()

        return jsonify({"success": True, "message": "Account created! You can now sign in."})

    except Exception as exc:
        print(f"[Auth] /register error: {exc}")
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500


@auth_routes.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        init_tables()
        data  = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()

        if not email:
            return jsonify({"success": False, "error": "Email address is required."})

        db  = get_db()
        row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        db.close()

        if not row:
            return jsonify({"success": False,
                            "error": "No account found with that email address."})

        code       = _gen_code()
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
        _reset_store[email] = {"code": code, "expires_at": expires_at}

        if not _send_code_email(email, code):
            return jsonify({"success": False,
                            "error": "Failed to send email. Check SMTP configuration."})

        return jsonify({"success": True, "message": "Reset code sent to your email."})

    except Exception as exc:
        print(f"[Auth] /forgot-password error: {exc}")
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500


@auth_routes.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        data     = request.get_json(silent=True) or {}
        email    = data.get("email", "").strip().lower()
        code     = data.get("code", "").strip().upper()
        password = data.get("password", "")

        if not all([email, code, password]):
            return jsonify({"success": False, "error": "All fields are required."})
        if len(password) < 6:
            return jsonify({"success": False,
                            "error": "Password must be at least 6 characters."})

        stored = _reset_store.get(email)
        if not stored:
            return jsonify({"success": False,
                            "error": "No active reset code found. Please request a new one."})
        if datetime.datetime.now() > stored["expires_at"]:
            _reset_store.pop(email, None)
            return jsonify({"success": False,
                            "error": "Reset code has expired. Please request a new one."})
        if stored["code"] != code:
            return jsonify({"success": False,
                            "error": "Incorrect reset code. Please check and try again."})

        init_tables()
        db = get_db()
        db.execute("UPDATE users SET password=? WHERE email=?", (_hash(password), email))
        db.commit()
        db.close()
        _reset_store.pop(email, None)

        return jsonify({"success": True, "message": "Password reset successfully. Please sign in."})

    except Exception as exc:
        print(f"[Auth] /reset-password error: {exc}")
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500