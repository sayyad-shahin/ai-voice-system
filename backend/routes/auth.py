"""
auth.py — VoiceAI Authentication
=================================
Routes:
  POST /auth              — login
  POST /register/request  — step 1: validate + send OTP to email
  POST /register/verify   — step 2: verify OTP + create account
  POST /forgot-password   — send reset code to email
  POST /reset-password    — verify reset code + update password

Security:
  - Passwords hashed with SHA-256
  - OTP codes: 6 chars (uppercase + digits), 10 min expiry
  - All logins/registrations logged to login_activity
"""

import os, random, string, hashlib, datetime, smtplib, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify
from config import get_db, init_tables

auth_routes   = Blueprint("auth", __name__)
SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

_otp_store:   dict = {}   # email → { code, expires_at, pending }
_reset_store: dict = {}   # email → { code, expires_at }


# ─── HELPERS ──────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _gen_code(k: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=k))

def _log(db, uid, username: str, action: str, ip: str = ""):
    try:
        db.execute(
            "INSERT INTO login_activity(user_id,username,action,ip) VALUES(?,?,?,?)",
            (uid, username, action, ip)
        )
    except Exception as e:
        print(f"[Auth] Log error: {e}")

def _email_html(code: str, heading: str, body: str) -> str:
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:auto;
                background:#07090f;color:#e8ecf4;padding:48px 40px;border-radius:20px;
                border:1px solid rgba(80,140,255,.15);">
      <h2 style="margin:0 0 4px;font-size:24px;font-weight:900;">VoiceAI</h2>
      <p style="color:#66748f;margin:0 0 28px;font-size:13px;">{heading}</p>
      <p style="margin:0 0 24px;line-height:1.8;">{body}</p>
      <div style="background:#0d1220;border:1px solid rgba(80,140,255,.25);
                  border-radius:14px;padding:32px;text-align:center;margin-bottom:28px;">
        <div style="font-size:44px;font-weight:900;letter-spacing:14px;
                    color:#3a7fff;font-family:'Courier New',monospace;">{code}</div>
        <p style="margin:10px 0 0;color:#66748f;font-size:13px;">Expires in 10 minutes</p>
      </div>
      <p style="color:#3d4a5c;font-size:12px;line-height:1.6;">
        If you did not request this, you can safely ignore this email.
      </p>
    </div>"""

def _send_email(to: str, subject: str, html: str) -> bool:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        # DEV fallback — extract and print code to console
        match = re.search(r'letter-spacing[^>]+>([A-Z0-9]{5,8})<', html)
        code  = match.group(1) if match else "CHECK HTML"
        print(f"\n{'='*55}")
        print(f"[DEV] Email to: {to}")
        print(f"[DEV] Subject : {subject}")
        print(f"[DEV] CODE    : {code}")
        print(f"{'='*55}\n")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SMTP_EMAIL, SMTP_PASSWORD)
            s.sendmail(SMTP_EMAIL, to, msg.as_string())
        print(f"[Auth] Email sent → {to}")
        return True
    except Exception as e:
        print(f"[Auth] Email error: {e}")
        return False


# ─── LOGIN ────────────────────────────────────────────────────

@auth_routes.route("/auth", methods=["POST"])
def auth():
    try:
        init_tables()
        d        = request.get_json(silent=True) or {}
        username = d.get("username", "").strip()
        password = d.get("password", "")
        ip       = request.remote_addr or ""

        if not username or not password:
            return jsonify({"success": False,
                            "error": "Please enter your username and password."})

        db  = get_db()
        row = db.execute(
            "SELECT id,username,name,password FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if not row:
            db.close()
            return jsonify({"success": False,
                            "error": "No account found. Please register first."})

        stored  = row["password"]
        matched = (stored == _hash(password)) or (stored == password)

        if not matched:
            _log(db, row["id"], username, "failed_login", ip)
            db.commit(); db.close()
            return jsonify({"success": False,
                            "error": "Incorrect password. Please try again."})

        if stored == password:  # upgrade plain → hash
            db.execute("UPDATE users SET password=? WHERE id=?",
                       (_hash(password), row["id"]))

        db.execute("UPDATE users SET last_login=? WHERE id=?",
                   (datetime.datetime.now().isoformat(), row["id"]))
        _log(db, row["id"], username, "login", ip)
        db.commit(); db.close()

        return jsonify({"success": True,
                        "username": row["username"],
                        "name":     row["name"]})
    except Exception as e:
        print(f"[Auth] /auth: {e}")
        return jsonify({"success": False, "error": "Server error."}), 500


# ─── REGISTER STEP 1 — validate + send OTP ────────────────────

@auth_routes.route("/register/request", methods=["POST"])
def register_request():
    try:
        init_tables()
        d        = request.get_json(silent=True) or {}
        name     = d.get("name", "").strip()
        email    = d.get("email", "").strip().lower()
        username = d.get("username", "").strip()
        password = d.get("password", "")

        if not all([name, email, username, password]):
            return jsonify({"success": False, "error": "All fields are required."})
        if "@" not in email or "." not in email.split("@")[-1]:
            return jsonify({"success": False,
                            "error": "Please enter a valid email address."})
        if len(password) < 6:
            return jsonify({"success": False,
                            "error": "Password must be at least 6 characters."})
        if len(username) < 3:
            return jsonify({"success": False,
                            "error": "Username must be at least 3 characters."})
        if not username.replace("_","").replace(".","").isalnum():
            return jsonify({"success": False,
                            "error": "Username: letters, numbers, _ and . only."})

        db = get_db()
        if db.execute("SELECT id FROM users WHERE username=?",
                      (username,)).fetchone():
            db.close()
            return jsonify({"success": False,
                            "error": "Username already taken. Please choose another."})
        if db.execute("SELECT id FROM users WHERE email=?",
                      (email,)).fetchone():
            db.close()
            return jsonify({"success": False,
                            "error": "An account with this email already exists."})
        db.close()

        code = _gen_code(6)
        _otp_store[email] = {
            "code":       code,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=10),
            "pending":    {"name": name, "email": email,
                           "username": username, "password": password}
        }

        html = _email_html(
            code,
            "Email Verification",
            "Enter this 6-character code to complete your VoiceAI registration."
        )
        if not _send_email(email, "VoiceAI — Verify your email", html):
            return jsonify({"success": False,
                            "error": "Failed to send verification email. Try again."})

        return jsonify({"success": True,
                        "message": "Verification code sent to your email."})
    except Exception as e:
        print(f"[Auth] /register/request: {e}")
        return jsonify({"success": False, "error": "Server error."}), 500


# ─── REGISTER STEP 2 — verify OTP + create account ────────────

@auth_routes.route("/register/verify", methods=["POST"])
def register_verify():
    try:
        init_tables()
        d     = request.get_json(silent=True) or {}
        email = d.get("email", "").strip().lower()
        code  = d.get("code", "").strip().upper()
        ip    = request.remote_addr or ""

        if not email or not code:
            return jsonify({"success": False,
                            "error": "Email and code are required."})

        stored = _otp_store.get(email)
        if not stored:
            return jsonify({"success": False,
                            "error": "No pending registration. Please start again."})
        if datetime.datetime.now() > stored["expires_at"]:
            _otp_store.pop(email, None)
            return jsonify({"success": False,
                            "error": "Code expired. Please register again."})
        if stored["code"] != code:
            return jsonify({"success": False,
                            "error": "Wrong code. Please check your email."})

        p  = stored["pending"]
        db = get_db()

        if db.execute("SELECT id FROM users WHERE username=?",
                      (p["username"],)).fetchone():
            db.close(); _otp_store.pop(email, None)
            return jsonify({"success": False,
                            "error": "Username was just taken. Please try a different one."})
        if db.execute("SELECT id FROM users WHERE email=?",
                      (email,)).fetchone():
            db.close(); _otp_store.pop(email, None)
            return jsonify({"success": False,
                            "error": "Account with this email already exists."})

        db.execute(
            "INSERT INTO users(name,username,password,email) VALUES(?,?,?,?)",
            (p["name"], p["username"], _hash(p["password"]), email)
        )
        db.commit()
        uid = db.execute("SELECT id FROM users WHERE username=?",
                         (p["username"],)).fetchone()["id"]
        _log(db, uid, p["username"], "register", ip)
        db.commit(); db.close()
        _otp_store.pop(email, None)

        return jsonify({"success": True,
                        "message": "Account created! You can now sign in."})
    except Exception as e:
        print(f"[Auth] /register/verify: {e}")
        return jsonify({"success": False, "error": "Server error."}), 500


# ─── FORGOT PASSWORD — send reset code ────────────────────────

@auth_routes.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        init_tables()
        d     = request.get_json(silent=True) or {}
        email = d.get("email", "").strip().lower()

        if not email:
            return jsonify({"success": False,
                            "error": "Email address is required."})

        db  = get_db()
        row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        db.close()

        if not row:
            return jsonify({"success": False,
                            "error": "No account found with that email."})

        code = _gen_code(6)
        _reset_store[email] = {
            "code":       code,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=10)
        }

        html = _email_html(
            code,
            "Password Reset Request",
            "Use this 6-character code to reset your VoiceAI password."
        )
        if not _send_email(email, "VoiceAI — Password Reset Code", html):
            return jsonify({"success": False,
                            "error": "Failed to send email. Please try again."})

        return jsonify({"success": True,
                        "message": "Reset code sent to your email."})
    except Exception as e:
        print(f"[Auth] /forgot-password: {e}")
        return jsonify({"success": False, "error": "Server error."}), 500


# ─── RESET PASSWORD ───────────────────────────────────────────

@auth_routes.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        d        = request.get_json(silent=True) or {}
        email    = d.get("email", "").strip().lower()
        code     = d.get("code", "").strip().upper()
        password = d.get("password", "")

        if not all([email, code, password]):
            return jsonify({"success": False, "error": "All fields are required."})
        if len(password) < 6:
            return jsonify({"success": False,
                            "error": "Password must be at least 6 characters."})

        stored = _reset_store.get(email)
        if not stored:
            return jsonify({"success": False,
                            "error": "No active reset request. Request a new code."})
        if datetime.datetime.now() > stored["expires_at"]:
            _reset_store.pop(email, None)
            return jsonify({"success": False,
                            "error": "Code expired. Please request a new one."})
        if stored["code"] != code:
            return jsonify({"success": False,
                            "error": "Wrong code. Please check your email."})

        init_tables()
        db = get_db()
        db.execute("UPDATE users SET password=? WHERE email=?",
                   (_hash(password), email))
        db.commit(); db.close()
        _reset_store.pop(email, None)

        return jsonify({"success": True,
                        "message": "Password reset! Please sign in."})
    except Exception as e:
        print(f"[Auth] /reset-password: {e}")
        return jsonify({"success": False, "error": "Server error."}), 500