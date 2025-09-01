# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, JournalEntry
import requests
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Paystack Configuration
paystack_secret_key = os.getenv('PAYSTACK_SECRET_KEY')
paystack_public_key = os.getenv('PAYSTACK_PUBLIC_KEY')

# Hugging Face API Setup
HF_API_URL = "https://api-inference.huggingface.co/models/joeddav/distilbert-base-uncased-go-emotions"
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------- Emotion Analysis -----------------
def analyze_sentiment(content):
    try:
        emotion_groups = {
            'Happy': ['joy', 'amusement', 'excitement', 'optimism', 'pride', 'gratitude', 'admiration', 'approval', 'caring', 'love'],
            'Sad': ['sadness', 'grief', 'disappointment', 'remorse'],
            'Angry': ['anger', 'annoyance', 'disapproval', 'disgust'],
            'Calm': ['neutral', 'relief', 'realization'],
            'Anxious': ['fear', 'nervousness', 'confusion', 'curiosity', 'desire', 'embarrassment', 'surprise']
        }

        content_lower = content.lower()
        typed_mood = None
        for mood in emotion_groups.keys():
            if mood.lower() in content_lower:
                typed_mood = mood
                break

        response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": content})
        sentiment_data = response.json()

        mood_scores = {mood: 0 for mood in emotion_groups}

        for item in sentiment_data:
            label = item.get('label', '').lower()
            score = item.get('score', 0)
            for mood, labels in emotion_groups.items():
                if label in labels:
                    mood_scores[mood] += score

        total = sum(mood_scores.values())
        if total > 0:
            for mood in mood_scores:
                mood_scores[mood] = (mood_scores[mood] / total) * 100
        else:
            result = simple_emotion_detection(content)
            result['typed_mood'] = typed_mood
            return result

        return {
            'labels': list(mood_scores.keys()),
            'scores': list(mood_scores.values()),
            'typed_mood': typed_mood
        }

    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        result = simple_emotion_detection(content)
        result['typed_mood'] = None
        return result

def simple_emotion_detection(content):
    content_lower = content.lower()
    emotion_keywords = {
        'Happy': ['happy', 'joy', 'excited', 'great', 'wonderful', 'amazing', 'love', 'good'],
        'Sad': ['sad', 'unhappy', 'depressed', 'down', 'miserable', 'grief', 'crying'],
        'Angry': ['angry', 'mad', 'furious', 'rage', 'annoyed', 'irritated'],
        'Calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil'],
        'Anxious': ['anxious', 'worried', 'nervous', 'stressed', 'afraid', 'scared']
    }

    mood_scores = {mood: 0 for mood in emotion_keywords.keys()}
    for mood, keywords in emotion_keywords.items():
        for keyword in keywords:
            mood_scores[mood] += content_lower.count(keyword)
    
    total = sum(mood_scores.values())
    if total > 0:
        for mood in mood_scores:
            mood_scores[mood] = (mood_scores[mood] / total) * 100
    else:
        for mood in mood_scores:
            mood_scores[mood] = 20

    return {
        'labels': list(mood_scores.keys()),
        'scores': list(mood_scores.values())
    }

# ----------------- Routes -----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.timestamp.desc()).limit(5).all()
    return render_template('index.html', entries=entries)

@app.route('/journal', methods=['GET','POST'])
@login_required
def journal():
    if not current_user.is_premium_active():
        entry_count = JournalEntry.query.filter_by(user_id=current_user.id).count()
        if entry_count >= 5:
            flash('Free tier limit reached. Upgrade to premium.')
            return redirect(url_for('premium'))

    if request.method == 'POST':
        content = request.form['content']
        sentiment_data = analyze_sentiment(content)

        entry = JournalEntry(
            user_id=current_user.id,
            content=content,
            mood_scores=sentiment_data,
            typed_mood=sentiment_data.get('typed_mood')
        )
        db.session.add(entry)
        db.session.commit()
        flash('Journal entry saved')
        return redirect(url_for('dashboard'))
    return render_template('journal.html')

@app.route('/history')
@login_required
def history():
    if not current_user.is_premium_active():
        entry_count = JournalEntry.query.filter_by(user_id=current_user.id).count()
        if entry_count >= 5:
            flash('Free tier limit reached. Upgrade to premium.')
            return redirect(url_for('premium'))

    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.timestamp.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_entry(id):
    entry = JournalEntry.query.get_or_404(id)
    if entry.user_id != current_user.id:
        return redirect(url_for('history'))

    if request.method == 'POST':
        content = request.form['content']
        sentiment_data = analyze_sentiment(content)

        entry.content = content
        entry.mood_scores = sentiment_data
        entry.typed_mood = sentiment_data.get('typed_mood')
        db.session.commit()
        flash('Entry updated')
        return redirect(url_for('history'))

    return render_template('journal.html', entry=entry)

@app.route('/delete/<int:id>')
@login_required
def delete_entry(id):
    entry = JournalEntry.query.get_or_404(id)
    if entry.user_id == current_user.id:
        db.session.delete(entry)
        db.session.commit()
        flash('Entry deleted')
    return redirect(url_for('history'))

# ----------------- Chart -----------------
@app.route('/chart')
@login_required
def chart():
    if not current_user.is_premium_active():
        entry_count = JournalEntry.query.filter_by(user_id=current_user.id).count()
        if entry_count >= 5:
            flash('Free tier limit reached. Upgrade to premium.')
            return redirect(url_for('premium'))
    return render_template('chart.html')

@app.route('/chart-data')
@login_required
def chart_data():
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    chart_type = request.args.get('type', 'line')

    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.timestamp >= start_date
    ).order_by(JournalEntry.timestamp.asc()).all()

    moods = ["Happy", "Sad", "Angry", "Calm", "Anxious"]
    colors = {
        'Happy': '#4CAF50',
        'Sad': '#2196F3',
        'Angry': '#F44336',
        'Calm': '#9C27B0',
        'Anxious': '#FF9800'
    }

    if chart_type == 'bar':
        mood_totals = {mood: [] for mood in moods}

        for entry in entries:
            mood_scores = entry.mood_scores
            if isinstance(mood_scores, str):
                try:
                    mood_scores = json.loads(mood_scores)
                except:
                    mood_scores = {'labels': moods, 'scores': [0]*5}

            typed_mood = getattr(entry, 'typed_mood', None)
            # Override all scores with typed_mood if exists
            if typed_mood in moods:
                mood_scores['scores'] = [100 if label == typed_mood else 0 for label in mood_scores['labels']]

            for mood in moods:
                idx = mood_scores['labels'].index(mood) if mood in mood_scores['labels'] else -1
                score = float(mood_scores['scores'][idx]) if idx >= 0 else 0
                mood_totals[mood].append(score)

        mood_averages = [sum(mood_totals[m])/len(mood_totals[m]) if mood_totals[m] else 0 for m in moods]
        chart_data = {
            'labels': moods,
            'datasets': [{
                'label': 'Average Mood Score (%)',
                'data': mood_averages,
                'backgroundColor': [colors[m] for m in moods],
                'borderColor': [colors[m] for m in moods],
                'borderWidth': 1
            }]
        }

    else:  # line chart
        chart_data = {
            'labels': [entry.timestamp.strftime('%Y-%m-%d') for entry in entries],
            'datasets': []
        }

        for mood in moods:
            mood_data = []
            for entry in entries:
                mood_scores = entry.mood_scores
                if isinstance(mood_scores, str):
                    try:
                        mood_scores = json.loads(mood_scores)
                    except:
                        mood_scores = {'labels': moods, 'scores': [0]*5}

                typed_mood = getattr(entry, 'typed_mood', None)
                # Override all scores with typed_mood if exists
                if typed_mood in moods:
                    mood_scores['scores'] = [100 if label == typed_mood else 0 for label in mood_scores['labels']]

                idx = mood_scores['labels'].index(mood) if mood in mood_scores['labels'] else -1
                score = float(mood_scores['scores'][idx]) if idx >= 0 else 0
                mood_data.append(score)

            chart_data['datasets'].append({
                'label': mood,
                'data': mood_data,
                'backgroundColor': colors[mood],
                'borderColor': colors[mood],
                'fill': False
            })

    return jsonify(chart_data)


# ----------------- Premium / Paystack -----------------
# ----------------- Premium / Paystack -----------------
@app.route('/premium')
@login_required
def premium():
    return render_template(
        'premium.html',
        paystack_key=paystack_public_key,
        is_premium=current_user.is_premium_active()
    )


@app.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_payment():
    data = request.get_json()
    amount_kes = data.get('amount')  # frontend sends amount in KES
    plan = data.get('plan', 'monthly')

    # Validate amount
    try:
        amount_kes = float(amount_kes)
        if amount_kes <= 0:
            return jsonify({'status': False, 'message': 'Invalid amount'}), 400
    except (ValueError, TypeError):
        return jsonify({'status': False, 'message': 'Invalid amount'}), 400

    # Convert KES to the smallest unit (cents)
    amount_cents = int(amount_kes * 100)

    payload = {
        "email": current_user.email,
        "amount": amount_cents,  # integer amount in KES cents
        "currency": "KES",
        "callback_url": url_for('verify_payment', _external=True),
        "metadata": {
            "user_id": current_user.id,
            "plan": plan
        }
    }

    headers = {
        "Authorization": f"Bearer {paystack_secret_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers
        )
        print("Paystack initialize response:", response.text)  # Debug log
        res_data = response.json()
        if res_data.get('status'):
            return jsonify({'status': True, 'message': 'Payment initialized', 'data': res_data['data']})
        return jsonify({'status': False, 'message': res_data.get('message', 'Payment initialization failed')}), 400

    except Exception as e:
        return jsonify({'status': False, 'message': f'Error initializing payment: {str(e)}'}), 500


@app.route('/verify-payment')
@login_required
def verify_payment():
    reference = request.args.get('reference')
    if not reference:
        flash('Invalid payment reference')
        return redirect(url_for('premium'))

    headers = {"Authorization": f"Bearer {paystack_secret_key}"}
    try:
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        data = response.json()

        if data.get('status') and data['data']['status'] == 'success':
            user_id = data['data']['metadata']['user_id']
            user = User.query.get(user_id)
            if user:
                user.is_premium = True
                user.premium_expiry = datetime.utcnow() + timedelta(days=30)
                db.session.commit()
                flash('Payment successful! Account upgraded to premium.')
                return redirect(url_for('dashboard'))
            flash('User not found')
            return redirect(url_for('premium'))
        flash('Payment verification failed')
        return redirect(url_for('premium'))

    except Exception as e:
        flash(f'Error verifying payment: {str(e)}')
        return redirect(url_for('premium'))


# ----------------- Debug -----------------
@app.route('/analyze-sentiment',methods=['POST'])
@login_required
def analyze_sentiment_debug():
    content=request.json.get('content','')
    return jsonify(analyze_sentiment(content))

# ----------------- Run -----------------
if __name__=='__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
