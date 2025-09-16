from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime, date
import secrets   # for generating secure key
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)

# ✅ Secret key (needed for flash + sessions)
app.secret_key = secrets.token_hex(16)   # generates a random secure key each run
# If you want it permanent, replace with a fixed string, e.g. "my_super_secret_key"

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:root@localhost/Todo_app"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "signup" 
#User model
class User(db.Model, UserMixin):
    __tablename__ = "users" 

    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email    = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

    todos = db.relationship('Todo', backref='user', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
# Create a database model for the Todo item
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    from_time = db.Column(db.String(50), nullable=False)
    to_time = db.Column(db.String(50), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    # Link to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"


with app.app_context():
    db.create_all()
# ----------------- Routes -----------------

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('create_todo'))  # logged-in users go to todo list
    else:
        return redirect(url_for('signup'))   
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        print("Signup Data:", username, email, password)

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "error")
            return redirect(url_for("signup"))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    # ⬇️ This must be at the same level as `if request.method == 'POST'`
    return render_template("Signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)  # ✅ log the user in
            flash("Login successful!", "success")
            return redirect(url_for("create_todo"))
        else:
            flash("Invalid credentials!", "error")
            return redirect(url_for("login"))

    return render_template("index.html", datetime=datetime)

@app.route('/todo', methods=['GET', 'POST'])
@login_required
def create_todo():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        from_time = request.form['from_time']
        to_time = request.form['to_time']
        date_created = request.form.get('date_created')  

        if date_created:
            date_created_obj = datetime.strptime(date_created, "%Y-%m-%d")
        else:
            date_created_obj = datetime.utcnow()

        todo = Todo(
            title=title,
            content=content,
            from_time=from_time,
            to_time=to_time,
            date_created=date_created_obj,
            user_id=current_user.id  # ✅ assign to logged-in user
        )

        db.session.add(todo)
        db.session.commit()

    today = date.today()
    
    # ✅ Only fetch todos for the current user
    todays_todos = Todo.query.filter_by(user_id=current_user.id)\
                             .filter(db.func.date(Todo.date_created) == today)\
                             .all()

    return render_template('index.html', allTodo=todays_todos, today=today, datetime=datetime)

# Delete a todo
@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    if todo and todo.date_created.date() < date.today():
        flash("❌ Cannot delete past tasks!", "warning")
        return redirect(request.referrer or url_for("create_todo"))
    db.session.delete(todo)
    db.session.commit()
    return redirect("/")


# Update a todo
@app.route('/update/<int:sno>', methods=['GET','POST'])
def update(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    if todo.date_created.date() < date.today():
        flash("❌ Cannot update past tasks!", "warning")
        return redirect(request.referrer or url_for("create_todo"))

    if request.method == 'POST':
        todo.title = request.form['title']
        todo.content = request.form['content']
        db.session.commit()
        return redirect("/")
    return render_template('update.html', todo=todo)


# Toggle completion
@app.route('/complete/<int:sno>', methods=['POST'])
def complete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    if todo and todo.date_created.date() < date.today():
        flash("❌ Cannot change status of past tasks!", "warning")
        return redirect(request.referrer or url_for("create_todo"))

    if todo:
        todo.completed = not todo.completed
        db.session.commit()

    return redirect(request.referrer or url_for("create_todo"))


# Calendar
@app.route('/calendar')
@login_required
def calendar():
    allTodo = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('calender.html', allTodo=allTodo)



@app.route('/events')
def events():
    todos = Todo.query.all()
    events = []
    for t in todos:
        events.append({
            "title": t.title,
            "start": t.date_created.strftime("%Y-%m-%d"),
            "extendedProps": {
                "description": t.content,
                "from_time": t.from_time,
                "to_time": t.to_time,
                "completed": t.completed
            },
            "color": "green" if t.completed else "navy",
            "textColor": "white",
            "borderColor": "white"
        })
    return jsonify(events)


@app.route('/todos_by_date/<date>')
def todos_by_date(date):
    selected_date = datetime.strptime(date, "%Y-%m-%d").date()
    todos = Todo.query.filter(db.func.date(Todo.date_created) == selected_date).all()
    return jsonify([
        {
            "title": t.title,
            "content": t.content,
            "from_time": t.from_time,
            "to_time": t.to_time
        } for t in todos
    ])


@app.route('/tasks')
def task_list():
    allTodo = Todo.query.all()
    return render_template('task_list.html', allTodo=allTodo,date=date)



@app.route('/pending')
def pending_tasks():
    todos = Todo.query.filter_by(completed=False).all()
    return render_template('task_list.html', allTodo=todos, title="Pending Tasks",date=date)


@app.route('/completed')
def completed_tasks():
    todos = Todo.query.filter_by(completed=True).all()
    return render_template('task_list.html', allTodo=todos, title="Completed Tasks",date=date)


# ----------------- Run -----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
