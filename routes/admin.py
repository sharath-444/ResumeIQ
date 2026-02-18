from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from models import db, User, Resume
from utils.decorators import admin_required

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    
    # Calculate Metrics
    avg_score = 0
    if resumes:
        total_score = sum(r.score for r in resumes)
        avg_score = round(total_score / len(resumes), 1)

    # Prepare Chart Data
    chart_labels = [r.filename for r in resumes[:10]] # limit to 10 recent
    chart_data = [r.score for r in resumes[:10]]
    
    return render_template('admin_dashboard.html', users=users, resumes=resumes, avg_score=avg_score, chart_labels=chart_labels, chart_data=chart_data)

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
