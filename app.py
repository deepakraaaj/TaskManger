from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField
from wtforms.validators import InputRequired, Length, EqualTo, DataRequired
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8)])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), Length(min=8), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    due_date = DateField('Due Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Create Task')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user)
        session['username'] = username  # Store username in session
        flash(f'Welcome back, {username}!')
        return redirect(url_for('dashboard', username=username))

    return render_template('login.html', form=form)

@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    if 'username' not in session or session['username'] != username:
        flash('Unauthorized access. Please log in.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found')
        return redirect(url_for('index'))

    return render_template('dashboard.html', username=username, tasks=user.tasks)

@app.route('/create_task/<username>', methods=['GET', 'POST'])
@login_required
def create_task(username):
    form = TaskForm()

    if 'username' not in session or session['username'] != username:
        flash('Unauthorized access. Please log in.')
        return redirect(url_for('login'))

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        due_date = form.due_date.data

        new_task = Task(title=title, description=description, due_date=due_date, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()

        flash('Task created successfully')
        return redirect(url_for('dashboard', username=username))

    return render_template('create_task.html', form=form)



@app.route('/update_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)

    if 'username' not in session or session['username'] != task.user.username:
        flash('Unauthorized access. Please log in.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()

        db.session.commit()
        flash('Task updated successfully')
        return redirect(url_for('dashboard', username=task.user.username))

    return render_template('update_task.html', task=task)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if 'username' not in session or session['username'] != task.user.username:
        flash('Unauthorized access. Please log in.')
        return redirect(url_for('login'))

    db.session.delete(task)
    db.session.commit()

    flash('Task deleted successfully')
    return redirect(url_for('dashboard', username=task.user.username))

# Download tasks as PDF
@app.route('/download_pdf/<username>')
@login_required
def download_pdf(username):
    if 'username' not in session or session['username'] != username:
        flash('Unauthorized access. Please log in.')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User not found')
        return redirect(url_for('index'))

    tasks = user.tasks  # Fetch all tasks for the user

    # PDF generation
    pdf = generate_pdf(tasks)

    # Send the PDF as a response for download
    return send_pdf_as_response(pdf)

def wrap_text(text, width, canvas, fontname="Helvetica", fontsize=12):
    """
    Wraps text to fit within a given width when drawn on the canvas.
    """
    wrapped_lines = []
    words = text.split()
    line = ""
    
    for word in words:
        test_line = line + word + " "
        if canvas.stringWidth(test_line, fontname, fontsize) <= width:
            line = test_line
        else:
            wrapped_lines.append(line.strip())
            line = word + " "
    wrapped_lines.append(line.strip())
    
    return wrapped_lines

def generate_pdf(tasks):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Set up header
    pdf.setLineWidth(0.5)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, 770, "Task List")
    pdf.line(30, 765, 570, 765)

    # Set up footer
    pdf.setFont("Helvetica", 10)
    pdf.drawString(30, 30, "Generated By Task Manager - Dheepworks")

    # Add quote and importance of to-do list
    pdf.setFont("Helvetica-Oblique", 10)
    quote = "The secret of getting ahead is getting started. - Mark Twain"
    importance = "Prioritize your tasks to stay organized and achieve your goals."
    quote_lines = wrap_text(quote, 540, pdf)
    importance_lines = wrap_text(importance, 540, pdf)
    
    y_quote = 50
    y_importance = y_quote + (len(quote_lines) + 1) * 12  # Adjust for each line of text

    for line in quote_lines:
        pdf.drawString(30, y_quote, line)
        y_quote -= 12

    for line in importance_lines:
        pdf.drawString(30, y_importance, line)
        y_importance -= 12

    # Content: Task table
    y_position = 700  # Initial y position for table
    row_height = 20
    table_start_y = y_position

    # Table headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, y_position, "Status")
    pdf.drawString(110, y_position, "Title")
    pdf.drawString(220, y_position, "Description")
    pdf.drawString(500, y_position, "Due Date")
    y_position -= row_height

    pdf.line(30, y_position, 570, y_position)  # Horizontal line under headers

    # Table content
    pdf.setFont("Helvetica", 12)
    col_widths = [80, 250, 100]  # Adjust column widths as needed

    for task in tasks:
        y_position -= row_height
        # Checkbox
        pdf.drawString(45, y_position + 10, "☐")
        # Task title
        pdf.drawString(110, y_position + 5, task.title)

        # Description with wrapping
        wrapped_description = wrap_text(task.description, col_widths[1], pdf)
        for line in wrapped_description:
            if y_position < y_importance:  # Check if nearing the importance section
                pdf.showPage()
                y_position = 750
                pdf.setFont("Helvetica", 12)
            pdf.drawString(220, y_position + 5, line)
            y_position -= row_height

        # Due date
        if y_position < y_importance:
            pdf.showPage()
            y_position = 750
            pdf.setFont("Helvetica", 12)
        pdf.drawString(500, y_position + 5, str(task.due_date))

    # Draw table borders
    pdf.rect(30, y_position - 20, 540, table_start_y - y_position + 40)

    pdf.save()
    buffer.seek(0)
    return buffer

# Function to send PDF as a response
def send_pdf_as_response(pdf):
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=task_list.pdf"}
    )
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
