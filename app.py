from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

# Data storage - in a real app, this would be a database
user_data = {
    'page_visits': [],
    'quiz_answers': {}
}

# Load learning content from JSON
def load_content():
    with open('static/data/content.json', 'r') as f:
        return json.load(f)

# Home route
@app.route('/')
def home():
    # Reset user data for new session
    user_data['page_visits'] = []
    user_data['quiz_answers'] = {}
    session['started'] = False
    return render_template('home.html')

# Start learning route
@app.route('/start')
def start():
    # Record that user started the learning process
    session['started'] = True
    user_data['page_visits'].append({
        'page': 'start',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    return redirect(url_for('learn', lesson_id=1))

# Learning route
@app.route('/learn/<int:lesson_id>', methods=['GET'])
def learn(lesson_id):
    if not session.get('started', False):
        return redirect(url_for('home'))
    
    content = load_content()
    if lesson_id < 1 or lesson_id > len(content['lessons']):
        return redirect(url_for('learn', lesson_id=1))
    
    # Record page visit
    user_data['page_visits'].append({
        'page': f'learn/{lesson_id}',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    lesson = content['lessons'][lesson_id-1]
    next_id = lesson_id + 1 if lesson_id < len(content['lessons']) else None
    
    # If we've gone through all lessons, go to quiz
    if next_id is None:
        next_url = url_for('quiz', question_id=1)
    else:
        next_url = url_for('learn', lesson_id=next_id)
    
    return render_template('learn.html', lesson=lesson, next_url=next_url, lesson_id=lesson_id)

# Quiz route
@app.route('/quiz/<int:question_id>', methods=['GET', 'POST'])
def quiz(question_id):
    if not session.get('started', False):
        return redirect(url_for('home'))
    
    content = load_content()
    if question_id < 1 or question_id > len(content['quiz']):
        return redirect(url_for('quiz', question_id=1))
    
    if request.method == 'POST':
        # Save the answer
        answer = request.form.get('answer')
        user_data['quiz_answers'][question_id] = {
            'answer': answer,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Go to next question or results
        if question_id < len(content['quiz']):
            return redirect(url_for('quiz', question_id=question_id+1))
        else:
            return redirect(url_for('results'))
    
    # Record page visit
    user_data['page_visits'].append({
        'page': f'quiz/{question_id}',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    question = content['quiz'][question_id-1]
    return render_template('quiz.html', question=question, question_id=question_id)

# Results route
@app.route('/results')
def results():
    if not session.get('started', False):
        return redirect(url_for('home'))
    
    content = load_content()
    score = 0
    answers = []
    
    for q_id, user_answer in user_data['quiz_answers'].items():
        q_idx = int(q_id) - 1
        if q_idx < len(content['quiz']):
            correct = content['quiz'][q_idx]['correct'] == user_answer['answer']
            if correct:
                score += 1
            answers.append({
                'question': content['quiz'][q_idx]['question'],
                'user_answer': user_answer['answer'],
                'correct_answer': content['quiz'][q_idx]['correct'],
                'is_correct': correct
            })
    
    # Record completion
    user_data['page_visits'].append({
        'page': 'results',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    return render_template('results.html', score=score, total=len(content['quiz']), answers=answers)

if __name__ == '__main__':
    app.run(debug=True)