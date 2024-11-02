from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from transformers import GPT2LMHeadModel, GPT2Tokenizer

app = Flask(__name__)
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use SQLite for simplicity
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


def generate_response(prompt):
    # Encode the input prompt
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    
    # Generate text
    outputs = model.generate(inputs, max_length=100, num_return_sequences=1)
    
    # Decode the generated text
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Use db.session.get() instead of User.query.get()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    result = ""
    if request.method == 'POST':
        prompt = request.form['prompt']  # Get the prompt from the form
        result = generate_response(prompt)  # Generate the response using GPT-2

    return render_template('dashboard.html', username=current_user.username, result=result)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)