from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime, date
import secrets   # for generating secure key

app = Flask(__name__)

# ✅ Secret key (needed for flash + sessions)
app.secret_key = secrets.token_hex(16)   # generates a random secure key each run
# If you want it permanent, replace with a fixed string, e.g. "my_super_secret_key"

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///ToDo.db"
db = SQLAlchemy(app)


# Create a database model for the Todo item
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    from_time = db.Column(db.String(50), nullable=False)
    to_time = db.Column(db.String(50), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"


# ----------------- Routes -----------------

@app.route('/', methods=['GET', 'POST'])
def create_todo():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        from_time = request.form['from_time']
        to_time = request.form['to_time']
        date_created = request.form.get('date_created')  

        if date_created:
            todo = Todo(
                title=title,
                content=content,
                from_time=from_time,
                to_time=to_time,
                date_created=datetime.strptime(date_created, "%Y-%m-%d")
            )
        else:
            todo = Todo(
                title=title,
                content=content,
                from_time=from_time,
                to_time=to_time
            )

        db.session.add(todo)
        db.session.commit()

    today = date.today()
    todays_todos = Todo.query.filter(db.func.date(Todo.date_created) == today).all()
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
def calendar():
    allTodo = Todo.query.all()
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        # Example check (replace with DB lookup later)
        if username == "admin" and password == "1234":
            flash("Login successful!", "success")
            return redirect(url_for("create_todo"))  # go to home page
        else:
            flash("Invalid credentials!", "error")

    return render_template("Signup.html") 
# ----------------- Run -----------------
if __name__ == '__main__':
    app.run(debug=True)
