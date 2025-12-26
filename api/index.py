from flask import Flask, render_template, request, redirect, url_for, session, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

MANAGER_ID = 'manager'
MANAGER_PASS = 'password123'

members = {}
current_period_start = datetime.now().replace(day=19) - timedelta(days=30)

def calculate_salary(member_name):
    if member_name not in members:
        return 0, 0, 0, 0

    attendance = members[member_name]['attendance']
    payments = members[member_name]['payments']

    days_present = sum(
        1 for date, present in attendance.items()
        if present and current_period_start <= datetime.strptime(date, '%Y-%m-%d') <
        current_period_start + timedelta(days=30)
    )

    total_earned = days_present * 300
    total_paid = sum(payments)
    remaining = total_earned - total_paid
    return days_present, total_earned, total_paid, remaining

def generate_pdf(member_name):
    d, e, p, r = calculate_salary(member_name)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Salary Statement - {member_name}")
    c.drawString(100, 720, f"Days Present: {d}")
    c.drawString(100, 690, f"Total Earned: ₹{e}")
    c.drawString(100, 660, f"Paid: ₹{p}")
    c.drawString(100, 630, f"Remaining: ₹{r}")
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['id'] == MANAGER_ID and request.form['password'] == MANAGER_PASS:
            session['logged_in'] = True
            return redirect(url_for('attendance'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        member = request.form['member']
        date = request.form['date']
        present = request.form.get('present') == 'on'

        if member not in members:
            members[member] = {'attendance': {}, 'payments': []}
        members[member]['attendance'][date] = present

    return render_template('attendance.html', members=members)

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form['new_member']
    if name not in members:
        members[name] = {'attendance': {}, 'payments': []}
    return redirect(url_for('attendance'))

@app.route('/add_payment', methods=['POST'])
def add_payment():
    member = request.form['member']
    amount = int(request.form['amount'])
    members[member]['payments'].append(amount)
    return redirect(url_for('member_detail', member=member))

@app.route('/member/<member>')
def member_detail(member):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    d, e, p, r = calculate_salary(member)
    return render_template('member.html', member=member, days=d, earned=e, paid=p, remaining=r)

@app.route('/download/<member>')
def download(member):
    return send_file(generate_pdf(member), as_attachment=True, download_name=f"{member}.pdf")
