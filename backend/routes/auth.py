import os, random, string, hashlib, datetime, smtplib, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, make_response
from config import get_db, init_tables

auth_routes   = Blueprint("auth", __name__)
SMTP_EMAIL    = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

_otp_store:   dict = {}
_reset_store: dict = {}


# ── CORS helper ────────────────────────────────────────────────────────────────
def _cors(data, status=200):
    """Wrap any dict/jsonify response with CORS headers."""
    resp = make_response(jsonify(data), status)
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return resp

def _options():
    """Handle OPTIONS preflight for any route."""
    resp = make_response("", 204)
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Max-Age"]        = "86400"
    return resp


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _hash(pw):   return hashlib.sha256(pw.encode()).hexdigest()
def _code(k=6):  return "".join(random.choices(string.ascii_uppercase + string.digits, k=k))

def _log(db, uid, username, action, ip=""):
    try:
        db.execute("INSERT INTO login_activity(user_id,username,action,ip) VALUES(?,?,?,?)",
                   (uid, username, action, ip))
    except: pass

def _email_html(code, heading, body_text):
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:auto;
                background:#04060d;color:#dde4f0;padding:48px 40px;border-radius:20px;
                border:1px solid rgba(45,114,240,.15);">
      <h2 style="margin:0 0 4px;font-size:22px;font-weight:800;">VoiceAI</h2>
      <p style="color:#5a6880;margin:0 0 28px;font-size:13px;">{heading}</p>
      <p style="margin:0 0 24px;line-height:1.8;">{body_text}</p>
      <div style="background:#070a14;border:1px solid rgba(45,114,240,.22);
                  border-radius:14px;padding:32px;text-align:center;margin-bottom:28px;">
        <div style="font-size:42px;font-weight:800;letter-spacing:14px;
                    color:#2d72f0;font-family:'Courier New',monospace;">{code}</div>
        <p style="margin:10px 0 0;color:#5a6880;font-size:13px;">Expires in 10 minutes</p>
      </div>
      <p style="color:#333e50;font-size:12px;">If you did not request this, ignore this email.</p>
    </div>"""

def _send(to, subject, html):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        m = re.search(r'>([A-Z0-9]{6})<', html)
        print(f"\n{'='*50}\n[DEV EMAIL] To: {to}\n[DEV EMAIL] Code: {m.group(1) if m else 'SEE HTML'}\n{'='*50}\n")
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


# ── LOGIN ──────────────────────────────────────────────────────────────────────

@auth_routes.route("/auth", methods=["POST", "OPTIONS"])
def auth():
    if request.method == "OPTIONS":
        return _options()
    try:
        init_tables()
        d        = request.get_json(silent=True) or {}
        username = d.get("username", "").strip()
        password = d.get("password", "")
        ip       = request.remote_addr or ""

        if not username or not password:
            return _cors({"success": False, "error": "Please enter username and password."})

        db  = get_db()
        row = db.execute(
            "SELECT id,username,name,password FROM users WHERE username=?", (username,)
        ).fetchone()

        if not row:
            db.close()
            return _cors({"success": False, "error": "No account found. Please register first."})

        stored  = row["password"]
        matched = (stored == _hash(password)) or (stored == password)

        if not matched:
            _log(db, row["id"], username, "failed_login", ip)
            db.commit(); db.close()
            return _cors({"success": False, "error": "Incorrect password."})

        if stored == password:
            db.execute("UPDATE users SET password=? WHERE id=?", (_hash(password), row["id"]))

        db.execute("UPDATE users SET last_login=? WHERE id=?",
                   (datetime.datetime.now().isoformat(), row["id"]))
        _log(db, row["id"], username, "login", ip)
        db.commit(); db.close()

        return _cors({"success": True, "username": row["username"], "name": row["name"]})

    except Exception as e:
        print(f"[Auth] /auth: {e}")
        return _cors({"success": False, "error": "Server error."}, 500)


# ── REGISTER STEP 1 ────────────────────────────────────────────────────────────

@auth_routes.route("/register/request", methods=["POST", "OPTIONS"])
def register_request():
    if request.method == "OPTIONS":
        return _options()
    try:
        init_tables()
        d        = request.get_json(silent=True) or {}
        name     = d.get("name", "").strip()
        email    = d.get("email", "").strip().lower()
        username = d.get("username", "").strip()
        password = d.get("password", "")

        if not all([name, email, username, password]):
            return _cors({"success": False, "error": "All fields are required."})
        if "@" not in email or "." not in email.split("@")[-1]:
            return _cors({"success": False, "error": "Please enter a valid email address."})
        if len(password) < 6:
            return _cors({"success": False, "error": "Password must be at least 6 characters."})
        if len(username) < 3:
            return _cors({"success": False, "error": "Username must be at least 3 characters."})
        if not username.replace("_", "").replace(".", "").isalnum():
            return _cors({"success": False, "error": "Username: letters, numbers, _ and . only."})

        db = get_db()
        if db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
            db.close()
            return _cors({"success": False, "error": "Username already taken."})
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            db.close()
            return _cors({"success": False, "error": "Email already registered."})
        db.close()

        otp = _code(6)
        _otp_store[email] = {
            "code":       otp,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=10),
            "pending":    {"name": name, "email": email, "username": username, "password": password}
        }

        html = _email_html(otp, "Email Verification",
                           "Enter this 6-character code to complete your VoiceAI registration.")
        if not _send(email, "VoiceAI — Verify your email", html):
            return _cors({"success": False, "error": "Failed to send verification email."})

        return _cors({"success": True, "message": "Verification code sent to your email."})

    except Exception as e:
        print(f"[Auth] /register/request: {e}")
        return _cors({"success": False, "error": "Server error."}, 500)


# ── REGISTER STEP 2 ────────────────────────────────────────────────────────────

@auth_routes.route("/register/verify", methods=["POST", "OPTIONS"])
def register_verify():
    if request.method == "OPTIONS":
        return _options()
    try:
        init_tables()
        d     = request.get_json(silent=True) or {}
        email = d.get("email", "").strip().lower()
        code  = d.get("code", "").strip().upper()
        ip    = request.remote_addr or ""

        if not email or not code:
            return _cors({"success": False, "error": "Email and code are required."})

        stored = _otp_store.get(email)
        if not stored:
            return _cors({"success": False,
                          "error": "No pending registration. Please register again."})
        if datetime.datetime.now() > stored["expires_at"]:
            _otp_store.pop(email, None)
            return _cors({"success": False, "error": "Code expired. Please register again."})
        if stored["code"] != code:
            return _cors({"success": False, "error": "Wrong code. Please check your email."})

        p  = stored["pending"]
        db = get_db()
        if db.execute("SELECT id FROM users WHERE username=?", (p["username"],)).fetchone():
            db.close(); _otp_store.pop(email, None)
            return _cors({"success": False, "error": "Username just taken. Try another."})
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            db.close(); _otp_store.pop(email, None)
            return _cors({"success": False, "error": "Email already registered."})

        db.execute("INSERT INTO users(name,username,password,email) VALUES(?,?,?,?)",
                   (p["name"], p["username"], _hash(p["password"]), email))
        db.commit()
        uid = db.execute("SELECT id FROM users WHERE username=?",
                         (p["username"],)).fetchone()["id"]
        _log(db, uid, p["username"], "register", ip)
        db.commit(); db.close()
        _otp_store.pop(email, None)

        return _cors({"success": True, "message": "Account created! You can now sign in."})

    except Exception as e:
        print(f"[Auth] /register/verify: {e}")
        return _cors({"success": False, "error": "Server error."}, 500)


# ── FORGOT PASSWORD ────────────────────────────────────────────────────────────

@auth_routes.route("/forgot-password", methods=["POST", "OPTIONS"])
def forgot_password():
    if request.method == "OPTIONS":
        return _options()
    try:
        init_tables()
        d     = request.get_json(silent=True) or {}
        email = d.get("email", "").strip().lower()

        if not email:
            return _cors({"success": False, "error": "Email address is required."})

        db  = get_db()
        row = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        db.close()

        if not row:
            return _cors({"success": False, "error": "No account found with that email."})

        otp = _code(6)
        _reset_store[email] = {
            "code":       otp,
            "expires_at": datetime.datetime.now() + datetime.timedelta(minutes=10)
        }

        html = _email_html(otp, "Password Reset",
                           "Use this 6-character code to reset your VoiceAI password.")
        if not _send(email, "VoiceAI — Password Reset Code", html):
            return _cors({"success": False, "error": "Failed to send email."})

        return _cors({"success": True, "message": "Reset code sent to your email."})

    except Exception as e:
        print(f"[Auth] /forgot-password: {e}")
        return _cors({"success": False, "error": "Server error."}, 500)


# ── RESET PASSWORD ─────────────────────────────────────────────────────────────

@auth_routes.route("/reset-password", methods=["POST", "OPTIONS"])
def reset_password():
    if request.method == "OPTIONS":
        return _options()
    try:
        d        = request.get_json(silent=True) or {}
        email    = d.get("email", "").strip().lower()
        code     = d.get("code", "").strip().upper()
        password = d.get("password", "")

        if not all([email, code, password]):
            return _cors({"success": False, "error": "All fields are required."})
        if len(password) < 6:
            return _cors({"success": False, "error": "Password must be at least 6 characters."})

        stored = _reset_store.get(email)
        if not stored:
            return _cors({"success": False,
                          "error": "No active reset request. Please request a new code."})
        if datetime.datetime.now() > stored["expires_at"]:
            _reset_store.pop(email, None)
            return _cors({"success": False, "error": "Code expired. Please request a new one."})
        if stored["code"] != code:
            return _cors({"success": False, "error": "Wrong code. Please check your email."})

        init_tables()
        db = get_db()
        db.execute("UPDATE users SET password=? WHERE email=?", (_hash(password), email))
        db.commit(); db.close()
        _reset_store.pop(email, None)

        return _cors({"success": True, "message": "Password reset! Please sign in."})

    except Exception as e:
        print(f"[Auth] /reset-password: {e}")
        return _cors({"success": False, "error": "Server error."}, 500)