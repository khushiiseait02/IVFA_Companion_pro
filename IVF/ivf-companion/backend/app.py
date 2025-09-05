from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from io import BytesIO
import datetime
from bson.objectid import ObjectId

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'ivf_secret_key'

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/ivf_db"
mongo = PyMongo(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        if mongo.db.users.find_one({'username': username}):
            flash("Username already exists.")
            return redirect('/register')

        mongo.db.users.insert_one({'username': username, 'password': password})
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({'username': request.form['username']})
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = str(user['_id'])
            return redirect('/dashboard')
        flash("Invalid login.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = ObjectId(session['user_id'])
    user = mongo.db.users.find_one({'_id': user_id})
    moods = list(mongo.db.mood_logs.find({'user_id': session['user_id']}))
    cycles = list(mongo.db.cycle_logs.find({'user_id': session['user_id']}))

    return render_template('dashboard.html', user=user, moods=moods, cycles=cycles)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    prediction = None
    if request.method == 'POST':
        age = int(request.form['age'])
        bmi = float(request.form['bmi'])

        if age < 30 and bmi < 25:
            prediction = "High"
        elif age < 35:
            prediction = "Moderate"
        else:
            prediction = "Low"

    return render_template('prediction.html', prediction=prediction)

@app.route('/mood', methods=['POST'])
def mood():
    if 'user_id' not in session:
        return redirect('/login')

    mood = request.form['mood']
    stress = int(request.form['stress'])

    mongo.db.mood_logs.insert_one({
        'mood': mood,
        'stress': stress,
        'date': datetime.date.today().isoformat(),
        'user_id': session['user_id']
    })

    return redirect('/dashboard')

@app.route('/cycle', methods=['POST'])
def cycle():
    if 'user_id' not in session:
        return redirect('/login')

    date = request.form['start_date']
    notes = request.form['notes']

    mongo.db.cycle_logs.insert_one({
        'start_date': date,
        'notes': notes,
        'user_id': session['user_id']
    })

    return redirect('/dashboard')

@app.route('/export')
def export():
    if 'user_id' not in session:
        return redirect('/login')

    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    moods = list(mongo.db.mood_logs.find({'user_id': session['user_id']}))
    cycles = list(mongo.db.cycle_logs.find({'user_id': session['user_id']}))

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, f"IVF Companion Report for {user['username']}")
    y = 780
    for mood in moods:
        p.drawString(100, y, f"{mood['date']}: Mood={mood['mood']}, Stress={mood['stress']}")
        y -= 20
    for cycle in cycles:
        p.drawString(100, y, f"{cycle['start_date']}: Notes={cycle['notes']}")
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='ivf_report.pdf', mimetype='application/pdf')

@app.route("/ivf-types")
def ivf_types():
    return render_template("types-of-ivf.html")

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json.get('message', '').lower()
    if "ivf" in message:
        response = "IVF stands for In Vitro Fertilization — a procedure to help with fertility or prevent genetic problems."
    elif "success rate" in message or "success" in message:
        response = "IVF success rates depend on age, BMI, and other medical factors. Would you like to try our success predictor above?"
    elif "hello" in message or "hi" in message:
        response = "Hi there! I'm your IVF Companion. Ask me anything about fertility or the IVF process."
    elif "bmi" in message:
        response = "BMI stands for Body Mass Index. It's one factor that can affect IVF success."
    elif "age" in message:
        response = "Age is a critical factor in IVF. Younger women generally have higher success rates."
    else:
        response = "I'm here to help with IVF-related questions. Try asking about success rate, age, or BMI."

    return jsonify({"response": response})

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/cycle-stage')
def cycle_stage():
    return render_template('ivf_content_engine.html')

@app.route('/ivf-cost-calculator', methods=['GET', 'POST'])
def ivf_cost_calculator():
     return render_template('ivf_cost_calculator.html')

@app.route('/mental-health-toolkit')
def mental_health_toolkit():
    return render_template('mental-health-toolkit.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
