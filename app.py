
from flask import Flask, render_template, redirect, url_for, flash, request, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import io
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///site.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ------------------ MODELS ------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    expenses = db.relationship('Expense', backref='author', lazy=True, cascade="all, delete-orphan")
    budget = db.relationship('Budget', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monthly_limit = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ ROUTES ------------------
@app.route("/")
@login_required
def dashboard():
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    end = datetime(now.year + (now.month // 12), ((now.month % 12) + 1), 1)

    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start,
        Expense.date < end
    ).all()

    total = sum(e.amount for e in expenses)
    budget_obj = current_user.budget
    budget_limit = budget_obj.monthly_limit if budget_obj else 0
    remaining = budget_limit - total
    percentage = (total / budget_limit * 100) if budget_limit > 0 else 0

    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    return render_template("dashboard.html",
                           total=total,
                           budget_limit=budget_limit,
                           remaining=remaining,
                           percentage=percentage,
                           labels=list(categories.keys()),
                           values=list(categories.values()),
                           expenses=expenses)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(username=request.form["username"],
                    email=request.form["email"])
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    expense = Expense(
        amount=float(request.form["amount"]),
        category=request.form["category"],
        description=request.form["description"],
        date=datetime.strptime(request.form["date"], "%Y-%m-%d"),
        author=current_user
    )
    db.session.add(expense)
    db.session.commit()
    flash("Expense added!", "success")
    return redirect(url_for("dashboard"))

@app.route("/edit_expense/<int:id>", methods=["POST"])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.author != current_user:
        abort(403)
    expense.amount = float(request.form["amount"])
    expense.category = request.form["category"]
    expense.description = request.form["description"]
    db.session.commit()
    flash("Expense updated!", "info")
    return redirect(url_for("dashboard"))

@app.route("/delete_expense/<int:id>", methods=["POST"])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.author != current_user:
        abort(403)
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted!", "warning")
    return redirect(url_for("dashboard"))

@app.route("/set_budget", methods=["POST"])
@login_required
def set_budget():
    limit = float(request.form["monthly_limit"])
    if current_user.budget:
        current_user.budget.monthly_limit = limit
    else:
        budget = Budget(monthly_limit=limit, user=current_user)
        db.session.add(budget)
    db.session.commit()
    flash("Budget updated!", "success")
    return redirect(url_for("dashboard"))

@app.route("/export")
@login_required
def export():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Category","Amount","Description"])
    for e in expenses:
        writer.writerow([e.date.strftime("%Y-%m-%d"), e.category, e.amount, e.description])
    return Response(output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=expenses.csv"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
