from flask import Flask, render_template, request, redirect, session, send_file
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from sklearn.linear_model import LogisticRegression
import numpy as np
import random

app = Flask(__name__)
app.secret_key = "secret123"

users = {}
otp_store = {}
students = []

# ML MODEL
X = np.array([
    [30, 60, 40],
    [80, 90, 85],
    [50, 70, 60],
    [20, 50, 30],
    [90, 95, 90]
])
y = ["High", "Low", "Medium", "High", "Low"]

model = LogisticRegression()
model.fit(X, y)


# LOGIN → GENERATE OTP
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in users and users[email] == password:
            otp = str(random.randint(1000, 9999))
            otp_store[email] = otp

            print("🔐 OTP:", otp)  # check terminal

            session['temp_user'] = email
            return redirect('/otp')
        else:
            return "Invalid login"

    return render_template('login.html')


# OTP VERIFY
@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        email = session.get('temp_user')

        if otp_store.get(email) == user_otp:
            session['user'] = email
            session.pop('temp_user', None)
            return redirect('/index')
        else:
            return "Invalid OTP"

    return render_template('otp.html')


# SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users[request.form['email']] = request.form['password']
        return redirect('/login')
    return render_template('signup.html')


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# INDEX
@app.route('/index')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')


# ANALYZE
@app.route('/analyze', methods=['POST'])
def analyze():
    global students
    students = []

    for i in range(1, 4):
        name = request.form.get(f'name{i}')
        marks = int(request.form.get(f'marks{i}', 0))
        attendance = int(request.form.get(f'attendance{i}', 0))
        assignments = int(request.form.get(f'assignments{i}', 0))

        result = model.predict([[marks, attendance, assignments]])[0]
        score = (marks * 0.5) + (attendance * 0.3) + (assignments * 0.2)

        # Python videos
        if score < 50:
            suggestion = "Learn Python basics"
            video = "https://www.youtube.com/embed/_uQrJ0TkZlc"
        elif score < 75:
            suggestion = "Practice Python coding"
            video = "https://www.youtube.com/embed/rfscVS0vtbw"
        else:
            suggestion = "Advanced Python"
            video = "https://www.youtube.com/embed/HGOBQPFzWKo"

        students.append({
            "name": name,
            "score": round(score, 2),
            "result": result,
            "suggestion": suggestion,
            "video": video
        })

    students = sorted(students, key=lambda x: x['score'], reverse=True)
    ranks = ["🥇 1st", "🥈 2nd", "🥉 3rd"]

    for i, s in enumerate(students):
        s['rank'] = ranks[i]

    names = [s['name'] for s in students]
    scores = [s['score'] for s in students]

    plt.figure()
    plt.bar(names, scores)
    plt.savefig("static/graph.png")
    plt.close()

    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    for s in students:
        risk_counts[s['result']] += 1

    plt.figure()
    plt.pie(risk_counts.values(), labels=risk_counts.keys(), autopct='%1.1f%%')
    plt.savefig("static/pie.png")
    plt.close()

    avg = sum(s['score'] for s in students) / len(students)

    return render_template("result.html", students=students, avg=round(avg, 2))


# PDF
@app.route('/download')
def download():
    doc = SimpleDocTemplate("static/report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Student Report", styles['Title']))
    content.append(Spacer(1, 20))

    table_data = [["Name", "Score", "Risk", "Rank"]]

    for s in students:
        table_data.append([s['name'], s['score'], s['result'], s['rank']])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    content.append(table)
    content.append(Spacer(1, 20))
    content.append(Image("static/graph.png", width=400, height=250))
    content.append(Spacer(1, 20))
    content.append(Image("static/pie.png", width=400, height=250))

    doc.build(content)

    return send_file("static/report.pdf", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)