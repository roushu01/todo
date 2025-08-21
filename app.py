from flask import Flask ,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime

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
    



@app.route('/',methods=['GET','POST'])
##above are the main steps
def create_todo():
   if request.method=='POST':
       title=request.form['title']
       content=request.form['content']
       from_time=request.form['from_time']
       to_time=request.form['To_time']


       todo=Todo(title=title,content=content,from_time=from_time,to_time=to_time)
       db.session.add(todo)
       db.session.commit()
   allTodo=Todo.query.all()
   
   return render_template('index.html',allTodo=allTodo)

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
##to do flask run
if __name__ =='__main__':
    app.run(debug=True)


