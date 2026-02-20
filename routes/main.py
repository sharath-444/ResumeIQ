from flask import Blueprint, render_template, request, jsonify, flash, current_app, redirect, url_for
from flask_login import login_required, current_user
import os
import secrets
from models import db, Resume
from utils.extractor import extract_text
from utils.scorer import calculate_ats_score
from utils.analyzer import parse_resume, analyze_skill_gap

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/builder')
@login_required
def builder():
    return render_template('builder.html')

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['resume']
    target_role = request.form.get('role', 'Frontend Developer')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and (file.filename.lower().endswith('.pdf') or file.filename.lower().endswith('.docx')):
        filename = secrets.token_hex(8) + "_" + file.filename
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process file
        try:
            text = extract_text(filepath)
            parsed_data = parse_resume(text)
            score, breakdown, feedback = calculate_ats_score(parsed_data)
            missing_skills = analyze_skill_gap(parsed_data['skills'], target_role)
            
            # Simple suggestions breakdown
            suggestions = {
                "strengths": [f"Found {len(parsed_data['skills'])} relevant skills."] if parsed_data['skills'] else [],
                "weaknesses": feedback,
                "missing_keywords": missing_skills,
                "improvements": ["Add measurable metrics to your achievements.", "Use strong action verbs."]
            }
            if score > 80:
                suggestions['strengths'].append("Great ATS score!")

            # Save to Database
            import json
            resume_entry = Resume(
                user_id=current_user.id,
                filename=file.filename,
                score=score,
                role_applied=target_role,
                analysis_data=json.dumps({
                    "score": score,
                    "breakdown": breakdown,
                    "details": parsed_data,
                    "suggestions": suggestions,
                    "role": target_role
                })
            )
            db.session.add(resume_entry)
            db.session.commit()

            result = {
                "score": score,
                "breakdown": breakdown,
                "details": parsed_data,
                "suggestions": suggestions,
                "role": target_role
            }
            return jsonify(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        return jsonify({'error': 'Invalid file type. Only PDF and DOCX allowed.'}), 400

@main.route('/result')
@login_required
def result():
    return render_template('result.html')

@main.route('/result/<int:resume_id>')
@login_required
def view_result(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    
    # Security: Ensure only the owner can view the report
    if resume.user_id != current_user.id:
        flash("You do not have permission to view this report.", "error")
        return redirect(url_for('main.dashboard'))
    
    # Parse the analysis data for the template
    import json
    analysis_data = json.loads(resume.analysis_data) if resume.analysis_data else {}
    
    return render_template('result.html', server_data=analysis_data)

@main.route('/dashboard')
@login_required
def dashboard():
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).all()
    # Parse JSON data for templates if needed, or just pass objects
    import json
    for r in resumes:
        if r.analysis_data:
            r.data = json.loads(r.analysis_data)
    return render_template('dashboard.html', resumes=resumes)

@main.route('/open-browser')
def open_browser_link():
    import webbrowser
    webbrowser.open('http://127.0.0.1:5000')
    return jsonify({'success': True})
