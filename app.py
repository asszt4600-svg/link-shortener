from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets
import os

app = Flask(__name__)

# إعداد قاعدة البيانات
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# الجداول
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    target_url = db.Column(db.Text)
    used = db.Column(db.Boolean, default=False)


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    link_id = db.Column(db.Integer)


# إنشاء قاعدة البيانات
with app.app_context():
    db.create_all()


# الصفحة الرئيسية (إنشاء رابط)
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"]

        code = secrets.token_urlsafe(5)

        link = Link(
            code=code,
            target_url=url
        )

        db.session.add(link)
        db.session.commit()

        # رابط صحيح (يشتغل محلي + Render)
        base_url = request.host_url.rstrip("/")
        return f"{base_url}/{code}"

    return render_template("index.html")


# فتح الرابط المختصر
@app.route("/<code>")
def open_link(code):
    link = Link.query.filter_by(code=code).first()

    if not link:
        print(f"[!] Unknown Link Attempt: {code}")
        return "Not Found", 404

    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 60)
    print("NEW VISITOR")
    print("=" * 60)
    print(f"Time       : {current_time}")
    print(f"IP         : {ip}")
    print(f"Short Link : {code}")
    print(f"Target URL : {link.target_url}")
    print(f"Browser    : {user_agent}")
    print("=" * 60)

    if link.used:
        print("[!] LINK EXPIRED")
        return render_template("expired.html")

    visit = Visit(
        ip=ip,
        link_id=link.id
    )

    db.session.add(visit)

    link.used = True

    db.session.commit()

    print("[+] Redirecting Visitor")

    return redirect(link.target_url)


# تشغيل السيرفر (مهم لـ Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)