from flask import Flask ,render_template,request,redirect,jsonify
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from datetime import date

app= Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///ToDo.db"
db=SQLAlchemy(app)

# Create a database model for the Todo item
class Todo(db.Model):
    sno=db.Column(db.Integer, primary_key=True)
    content=db.Column(db.String(500), nullable=False)
    title=db.Column(db.String(200), nullable=False)
    date_created=db.Column(db.DateTime ,default=datetime.utcnow)
    from_time=db.Column(db.String(50),nullable=False)
    to_time=db.Column(db.String(50),nullable=False)
    completed=db.Column(db.Boolean,default=False)
# it is for the database to know how to represent the object
    def __repr__(self)->str:
        return f"{self.sno} -{self.title}"
    

@app.route('/', methods=['GET', 'POST'])
def create_todo():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        from_time = request.form['from_time']
        to_time = request.form['to_time']
        date_created = request.form.get('date_created')  # safe access

        if date_created:  # user selected a date
            todo = Todo(
                title=title,
                content=content,
                from_time=from_time,
                to_time=to_time,
                date_created=datetime.strptime(date_created, "%Y-%m-%d")
            )
        else:  # no date provided → use default (today)
            todo = Todo(
                title=title,
                content=content,
                from_time=from_time,
                to_time=to_time
            )

        db.session.add(todo)
        db.session.commit()

    # 🔹 Only fetch today's todos
    today = date.today()
    todays_todos = Todo.query.filter(db.func.date(Todo.date_created) == today).all()

    return render_template('index.html', allTodo=todays_todos, today=today,datetime=datetime)


@app.route('/delete/<int:sno>')
def delete(sno):
    todo=Todo.query.filter_by(sno=sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect("/")
@app.route('/update/<int:sno>',methods=['GET','POST'])
def update(sno):
   if request.method=='POST':
       title=request.form['title']
       content=request.form['content']

       todo=Todo.query.filter_by(sno=sno).first()
       todo.title=title
       todo.content=content
       db.session.add(todo)
       db.session.commit()
       return redirect("/")
   todo=Todo.query.filter_by(sno=sno).first()
   return render_template('update.html',todo=todo)
@app.route('/complete/<int:sno>', methods=['POST'])
def complete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    if todo:
        todo.completed = not todo.completed
        db.session.commit()
    return redirect('/')
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
                "completed":t.completed
            }
        })
    return jsonify(events)
@app.route('/todos_by_date/<date>')
def todos_by_date(date):
    # Parse the date string "YYYY-MM-DD"
    selected_date = datetime.strptime(date, "%Y-%m-%d").date()
    todos = Todo.query.filter(
        db.func.date(Todo.date_created) == selected_date
    ).all()
    return jsonify([
        {
            "title": t.title,
            "content": t.content,
            "from_time": t.from_time,
            "to_time": t.to_time
        } for t in todos
    ])


##to do flask run
if __name__ =='__main__':
    app.run(debug=True)


