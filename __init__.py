from flask import Flask, render_template, redirect, url_for, session, request, jsonify, flash, g
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_sqlalchemy import SQLAlchemy
import random
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)

# SQL Tables

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True, nullable = False)
	email = db.Column(db.String(40), unique = True, nullable = False)
	password = db.Column(db.String(20), nullable = False)
	name = db.Column(db.String(20), nullable = False)
	dash = db.relationship('Dashboard', backref = 'Student', lazy = True)
	sk = db.relationship('Skills', backref = 'studs', lazy = True)

	def __repr__(self):
		return f"User('{self.email}', '{self.password}','{self.name}')"

class Category(db.Model):
	id = db.Column(db.Integer, primary_key = True, nullable = False)
	category_name = db.Column(db.String(20), nullable = False, default = 'Verbal')
	category_time = db.Column(db.Integer, default = 15)
	questions = db.relationship('Question', backref = 'category_ques', lazy = True)

	def __repr__(self):
		return f"Category('{self.category_name}','{self.category_time}')"

class Question(db.Model):
	id = db.Column(db.Integer, primary_key = True, nullable = False)
	question = db.Column(db.String(60), nullable = False, unique = True)
	image = db.Column(db.String(200))
	correct_answer = db.Column(db.String(200))
	wrong_ans_1 = db.Column(db.String(200))
	wrong_ans_2 = db.Column(db.String(200))
	wrong_ans_3 = db.Column(db.String(200))
	category_question = db.Column(db.String(20), db.ForeignKey('category.category_name'), nullable = False)

	def __repr__(self):
		return f"Question('{self.question}','{self.image}','{self.correct_answer}','{self.wrong_ans_1}','{self.wrong_ans_2}','{self.wrong_ans_3}','{self.category_question}')"

class Dashboard(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	stud = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
	image = db.Column(db.String(50))
	resume = db.Column(db.String(50))

	def __repr__(self):
		return f"Dashboard('{self.stud}', '{self.image}', '{self.resume}')"

class Skills(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	skill = db.Column(db.String(20))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

	def __repr__(self):
		return f"Skills('{self.skill}','{self.user_id}')"

# Flask Form

class FileForm(FlaskForm):
	img = FileField('Add images(if any)', validators=[FileAllowed(['jpg', 'png','gif','jpeg'])])

# Image Storing Functions

def func(images, name):
	random_hex = name
	_, file_ext = os.path.splitext(images.filename)
	pic_fn = random_hex + file_ext
	pic_path = os.path.join(app.root_path, 'static/img/ques',pic_fn)
	images.save(pic_path)

	return pic_fn

def displaypic(images, name):
	random_hex = name
	_, file_ext = os.path.splitext(images.filename)
	pic_fn = random_hex + file_ext
	pic_path = os.path.join(app.root_path, 'static/img/users',pic_fn)
	images.save(pic_path)

	return pic_fn

def removepic(images, name):
	random_hex = name
	_, file_ext = os.path.splitext(images.filename)
	pic_fn = random_hex + file_ext
	pic_path = os.path.join(app.root_path, 'static/img/users',pic_fn)
	os.remove(pic_path)

	return pic_fn

# Routes
@app.before_request
def before_request():
	g.user = None
	if 'username' in session == 'admin':
		g.user = 'admin'

@app.route('/', methods=['POST','GET'])
def index():
	session['username'] = None
	if request.method == 'POST':
		if request.form['test'] == 'signup':
			#Create New User
			try:
				me = User(email = request.form['email'], password = request.form['pass'], 
				name = request.form['fname']+' '+request.form['lname'])
				db.session.add(me)
				db.session.commit()
				return render_template('index.html', msg='Successfully Registered!')
			except:
				return render_template('index.html', msg='There was a problem creating your Account')
		if request.form['test'] == 'login':
			#Login 
			if request.form['lemail'] == 'admin' and request.form['lpass'] == 'admin':
				user = 'admin'
				session['username'] = user
				return redirect(url_for('admi',user=user))
			check = User.query.filter_by(email = request.form['lemail']).first()
			if check:
				try:
					authu = check.email
					authp = check.password
					if authu == request.form['lemail'] and authp == request.form['lpass']:
						user = check.name
						session['username'] = user
						return redirect(url_for('dashboard', user=user))
					else:
						error = "Password didn't matched"
						return render_template('index.html', error=error)
				except:
					error = "There was something wrong!"
					return render_template('index.html', error=error)
			else:
				error = "No Account Found with " + request.form['lemail']
			return render_template('index.html', error=error)
	return render_template('index.html')

#Student Dashboard

@app.route('/dashboard/<user>', methods=['POST','GET'])
def dashboard(user):
	if g.user:
		if session['username']:
			form = FileForm()
			lst = []
			try:
				u = User.query.filter_by(name = user).first()
				s = Skills.query.filter_by(user_id = u.id)
				p = Dashboard.query.filter_by(stud = u.id).first()
				if p:
					pr = p.image
				else:
					pr = 'default.png'
				for i in s:
					lst.append(i.skill)
			except:
				flash('There are some errors with your Account','danger')
				return render_template('dash.html', user=user, lst=lst)
			if request.method =='POST':
				pro = form.img.data
				if request.form['skills'] is not None:
					data = request.form['skills']
					for x in data.split(','):
						x.strip()
						d = Skills(skill = x, user_id = u.id)
						db.session.add(d)
				if pro:
					try:
						removepic(pro, str(u.id))
						form_data = displaypic(pro, str(u.id))
					except:
						flash('Photo can\'t be uploaded','warning')
						return render_template('dash.html', user=user, lst=lst)
				else:
					form_data = 'default.png'
				try:
					new = Dashboard.query.filter_by(stud = u.id).update({Dashboard.image:form_data, Dashboard.resume:request.form['resume']})
					db.session.commit()
					return redirect(url_for('dashboard', user=user, lst=lst, form=form, pr=pr))
				except:
					flash('Error saving your data in database','danger')
					return redirect(url_for('dashboard', user=user, lst=lst, form=form, pr=pr))
			return render_template('dash.html', user=user, lst=lst, form=form, pr=pr)
		return redirect(url_for('index'))
	return redirect(url_for('index'))

#Main Test

@app.route('/<user>/<category>', methods=['POST','GET'])
def test(user,category):
	if g.user:
		if session['username']:
			cat = Category.query.filter_by(category_name = category).first()
			qu = list(Question().query.filter_by(category_question = cat.category_name)) 
			temp = 1
			b = []
			cor_ans = []
			for items in qu:
				a = {}
				ans = Question().query.filter_by(id = temp).first()
				ans_list = []
				ans_list.append(ans.correct_answer)
				cor_ans.append(ans.correct_answer)
				ans_list.append(ans.wrong_ans_1)
				ans_list.append(ans.wrong_ans_2)
				ans_list.append(ans.wrong_ans_3)
				random.shuffle(ans_list)
				a['question'] = ans.question
				a['answers'] = ans_list
				a['image'] = ans.image
				b.append(a)
				temp+=1
			# Number of Questions to be selected
			ques = list(random.sample(b, 5))
			if request.method == 'POST':
				score = 0
				count = [1]
				try:
					for i in range(1,3):
						for elem in cor_ans:
							name = request.form.get(str(count), None)
							if name is None:
								score+=0
							elif request.form[str(count)] == elem:
								score+=10
						count.append(count.pop() + 1)
					return render_template('score.html', score=score, user=user)
				except:
					flash('Error Occured!','warning')
					t = cat.category_time
					return render_template('login.html', ques=ques, t=t,user=user)
			t = cat.category_time
			return render_template('login.html', ques=ques, t=t,user=user)
		war = 'Please Login!'
		return render_template('index.html', war=war)
	return redirect(url_for('index', user=None, war='You can\'t login now!'))

#Admin Routes

@app.route('/<user>', methods=['POST','GET'])
def admi(user):
	if session['username'] == 'admin':
		form = FileForm()
		if request.method == 'POST':
			images = form.img.data
			name = request.form['ques']
			if images:
				ffilee = func(images, name)
			else:
				ffilee = None
			answer_list = []
			answer_list.append(request.form['coans'])
			for i in range(1,4):
				answer_list.append(request.form[str(i)+'ans'])
			try:
				category = Question(question = request.form['ques'],image = ffilee, correct_answer = request.form['coans'],
					wrong_ans_1 = request.form['1ans'], wrong_ans_2 = request.form['2ans'], 
					wrong_ans_3 = request.form['3ans'], category_question = request.form['cat'])
				db.session.add(category)
				db.session.commit()
				flash('Added Successfully!' , 'success')
				return render_template('admin.html',user=user, form=form)
			except:
				flash('Can\'t find the specified category ☹' , 'warning')
				return render_template('admin.html',user=user, form=form)
		return render_template('admin.html',user=user, form=form)
	return redirect(url_for('index', user=None))

@app.route('/<user>/<score>/final-result')
def result(user,score):
	if g.user:
		if session['username']:
			return render_template('score.html',score=score, user=user)
		return redirect('url_for'('index'))
	return redirect(url_for('index', user=None, war='You can\'t login now!'))

@app.route('/<user>/categories', methods = ['POST','GET'])
def categories(user):
	if session['username'] == 'admin':
		if request.method == 'POST':
			try:
				new = request.form['category']
				updated = Category.query.filter_by(category_name = new).update({Category.category_time:request.form['cat_time']})
				db.session.commit()
				return redirect(url_for('categories',user=user))
			except:
				flash('ERROR HERE 😣', 'error')
				return redirect(url_for('categories',user=user))
		return render_template('categories.html', user=user)
	return redirect(url_for('index'))

@app.route('/<user>/allusers')
def allusers(user):
	if session['username'] == 'admin':
		use = User.query.all()
		return render_template('users.html', use=use)
	return redirect(url_for('index'))

@app.route('/<user>/<int:roll>')
def stats(user,roll):
	if session['username'] == 'admin':
		form = FileForm()
		u = User.query.filter_by(id = roll).first()
		lst = []
		s = Skills.query.filter_by(user_id = u.id)
		p = Dashboard.query.filter_by(stud = u.id).first()
		if p:
			pr = p.image
		else:
			pr = 'default.png'
		for i in s:
			lst.append(i.skill)
		return render_template('stats.html',user=user, u=u, pr=pr,lst=lst, form=form,p=p)
	return redirect(url_for('index'))

@app.route('/logout')
def logout():
	session['username'] == None
	return redirect(url_for('index'))

if __name__ == '__main__':
	app.run(debug=True)