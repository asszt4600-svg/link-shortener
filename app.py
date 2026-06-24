from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    target_url = db.Column(db.Text)
    used = db.Column(db.Boolean, default=False)


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    link_id = db.Column(db.Integer)


with app.app_context():
    db.create_all()


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

        return f"http://127.0.0.1:5000/{code}"

    return render_template("index.html")


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


if __name__ == "__main__":
    app.run(debug=True)