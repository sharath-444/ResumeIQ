from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_mail import Mail, Message
from utils.decorators import admin_required
from models import db, User, Resume, SMTPConfig, ParsedData
from utils.constants import get_all_roles, TARGET_ROLES
from utils.extractor import extract_text
from utils.scorer import calculate_ats_score
from utils.analyzer import parse_resume, analyze_skill_gap
import uuid
import os
import json

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    
    # Calculate Metrics
    avg_score = 0
    shortlisted_count = Resume.query.filter_by(is_shortlisted=True).count()
    
    if resumes:
        total_score = sum(r.score for r in resumes)
        avg_score = round(total_score / len(resumes), 1)

    # Prepare Chart Data
    chart_labels = [r.filename for r in resumes[:10]] # limit to 10 recent
    chart_data = [r.score for r in resumes[:10]]
    
    return render_template('admin_dashboard.html', 
                          users=users, 
                          resumes=resumes, 
                          avg_score=avg_score, 
                          shortlisted_count=shortlisted_count,
                          chart_labels=chart_labels, 
                          chart_data=chart_data)

@admin.route('/candidates')
@login_required
@admin_required
def candidates():
    from utils.constants import get_all_roles, TARGET_ROLES
    role = request.args.get('role', 'All')
    score_min = request.args.get('score_min', 0, type=int)
    batch_id = request.args.get('batch_id')
    
    query = Resume.query
    
    if batch_id:
        query = query.filter_by(batch_id=batch_id)
    elif role == 'All' and score_min == 0:
        # If no filters and no batch, show empty or latest 5 with a message
        # For now, let's show nothing if batch_id is not provided but requested filters are empty
        query = query.filter(Resume.id == -1) # return empty
    
    if role != 'All':
        query = query.filter_by(role_applied=role)
    
    if score_min > 0:
        query = query.filter(Resume.score >= score_min)
        
    candidates = query.order_by(Resume.score.desc()).all()
    
    # Get all possible roles from constants
    roles = get_all_roles()
    
    return render_template('admin_candidates.html', 
                          candidates=candidates, 
                          roles=roles, 
                          target_roles=TARGET_ROLES,
                          selected_role=role,
                          selected_score=score_min,
                          selected_batch=batch_id)

@admin.route('/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload():
    if request.method == 'POST':
        files = request.files.getlist('resumes')
        target_role = request.form.get('role', 'Software Engineer')
        
        if not files or files[0].filename == '':
            flash('No files selected', 'error')
            return redirect(url_for('admin.upload'))
            
        batch_id = str(uuid.uuid4())[:8]
        processed_count = 0
        
        for file in files:
            if file and file.filename.lower().endswith(('.pdf', '.docx')):
                import secrets
                safe_name = secrets.token_hex(8) + '_' + file.filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_name)
                file.save(filepath)
                file_size = os.path.getsize(filepath)
                
                try:
                    text = extract_text(filepath)
                    parsed_data = parse_resume(text)
                    score, breakdown, feedback = calculate_ats_score(parsed_data, target_role)
                    missing_skills = analyze_skill_gap(parsed_data['skills'], target_role)
                    
                    from utils.analyzer import generate_ai_tips
                    dynamic_tips = generate_ai_tips(parsed_data)

                    suggestions = {
                        'strengths': ([f"Found {len(parsed_data['skills'])} relevant skills."]
                                      if parsed_data['skills'] else []),
                        'weaknesses': feedback,
                        'missing_keywords': missing_skills,
                        'improvements': dynamic_tips,
                    }
                    
                    analysis_json = json.dumps({
                        'score': score,
                        'breakdown': breakdown,
                        'details': parsed_data,
                        'suggestions': suggestions,
                        'role': target_role,
                    })

                    resume_entry = Resume(
                        user_id=current_user.id,
                        filename=file.filename,
                        filepath=safe_name,
                        file_size=file_size,
                        score=score,
                        role_applied=target_role,
                        analysis_data=analysis_json,
                        batch_id=batch_id
                    )
                    db.session.add(resume_entry)
                    db.session.flush()

                    parsed_entry = ParsedData(
                        resume_id=resume_entry.id,
                        name=parsed_data.get('name'),
                        email=parsed_data.get('email'),
                        phone=parsed_data.get('phone'),
                        skills=json.dumps(parsed_data.get('skills', [])),
                        experience=json.dumps(parsed_data.get('experience', [])),
                        education=json.dumps(parsed_data.get('education', [])),
                        raw_text=text[:10000],
                    )
                    db.session.add(parsed_entry)
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing {file.filename}: {e}")
                    
        db.session.commit()
        flash(f'Successfully processed {processed_count} resumes in batch {batch_id}', 'success')
        return redirect(url_for('admin.candidates', batch_id=batch_id))
        
    return render_template('admin_upload.html', target_roles=TARGET_ROLES)

@admin.route('/toggle_shortlist/<int:resume_id>')
@login_required
@admin_required
def toggle_shortlist(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    resume.is_shortlisted = not resume.is_shortlisted
    db.session.commit()
    
    flash(f"Candidate {'shortlisted' if resume.is_shortlisted else 'removed from shortlist'}", 'success')
    return redirect(request.referrer or url_for('admin.candidates'))

@admin.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete admin user', 'error')
        return redirect(url_for('admin.dashboard'))
    
    try:
        # Delete associated resumes first (though cascade usually handles this)
        Resume.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting user: {e}', 'error')
    
    return redirect(url_for('admin.dashboard'))

@admin.route('/delete_resume/<int:resume_id>')
@login_required
@admin_required
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    try:
        db.session.delete(resume)
        db.session.commit()
        flash('Resume deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting resume: {e}', 'error')
        
    return redirect(url_for('admin.dashboard'))

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    config = SMTPConfig.query.first()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        server = request.form.get('server')
        port = int(request.form.get('port'))
        username = request.form.get('username')
        password = request.form.get('password')
        use_tls = 'use_tls' in request.form
        
        if not config:
            config = SMTPConfig(server=server, port=port, username=username, password=password, use_tls=use_tls)
            db.session.add(config)
        else:
            config.server = server
            config.port = port
            config.username = username
            config.password = password
            config.use_tls = use_tls
            
        db.session.commit()
        
        if action == 'save':
            flash('Settings saved successfully', 'success')
        elif action == 'test':
            # Send Test Email
            from flask import current_app
            
            # Configure Mail dynamically
            current_app.config['MAIL_SERVER'] = config.server
            current_app.config['MAIL_PORT'] = config.port
            current_app.config['MAIL_USERNAME'] = config.username
            current_app.config['MAIL_PASSWORD'] = config.password
            current_app.config['MAIL_USE_TLS'] = config.use_tls
            current_app.config['MAIL_USE_SSL'] = False
            
            mail = Mail(current_app)
            try:
                msg = Message("ResumeIQ Test Email", 
                            sender=config.username, 
                            recipients=[current_user.username if '@' in current_user.username else config.username])
                msg.body = "This is a test email to verify your SMTP settings."
                mail.send(msg)
                flash(f'Test email sent to {msg.recipients[0]}', 'success')
            except Exception as e:
                flash(f'Failed to send email: {e}', 'error')
                
        return redirect(url_for('admin.settings'))
        
    return render_template('admin_settings.html', config=config)
