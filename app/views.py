from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import io
import base64
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from app import mongo
from app.models import User, Question, ExamResult, Subject
from app.utils import import_from_docx
from bson import ObjectId

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        subjects = Subject.get_all()
        # Add question count to each subject
        for subject in subjects:
            subject['question_count'] = Subject.count_questions(subject['_id'])
            # Add user stats per subject
            stats = ExamResult.get_user_stats(current_user.id, subject['_id'])
            if stats:
                subject['user_stats'] = stats
                
        total_questions = Question.count()
        overall_stats = ExamResult.get_user_stats(current_user.id)
        
        return render_template('index.html', 
                             user=current_user, 
                             subjects=subjects,
                             total_questions=total_questions,
                             stats=overall_stats)
    return redirect(url_for('auth.login'))

@main_bp.route('/exam')
@login_required
def exam():
    # Get parameters from request
    limit_arg = request.args.get('limit', '20')
    subject_id = request.args.get('subject_id')
    
    try:
        time_limit = int(request.args.get('time', '20'))
    except ValueError:
        time_limit = 20
    
    if limit_arg == 'all':
        if subject_id:
            questions = Question.get_by_subject(subject_id)
        else:
            questions = Question.get_all()
    else:
        try:
            limit = int(limit_arg)
        except ValueError:
            limit = 20
        questions = Question.get_random_questions(limit=limit, subject_id=subject_id)
    
    if len(questions) < 1:
        flash('Không có câu hỏi nào trong ngân hàng cho môn học này.', 'warning')
        return redirect(url_for('main.index'))
    
    subject_name = "Tổng hợp"
    if subject_id:
        subject = Subject.get(subject_id)
        if subject:
            subject_name = subject['name']
            
    return render_template('exam.html', questions=questions, time_limit=time_limit, subject_name=subject_name, subject_id=subject_id)

@main_bp.route('/submit_exam', methods=['POST'])
@login_required
def submit_exam():
    data = request.json
    answers = data.get('answers', {})
    duration = data.get('duration', 0)
    subject_id = data.get('subject_id')
    
    # Calculate score
    score = 0
    detailed_answers = []
    
    for qid, user_answer in answers.items():
        try:
            question = mongo.db.questions.find_one({'_id': ObjectId(qid)})
            if question:
                is_correct = (user_answer == question['correct_answer'])
                if is_correct:
                    score += 1
                
                detailed_answers.append({
                    'question_id': str(question['_id']),
                    'question': question['question'],
                    'user_answer': user_answer,
                    'correct_answer': question['correct_answer'],
                    'is_correct': is_correct,
                    'options': question['options']
                })
        except:
            continue
    
    total_questions = len(detailed_answers)
    
    # Save result
    result_id = ExamResult.create(
        user_id=current_user.id,
        score=score,
        total_questions=total_questions,
        answers=detailed_answers,
        duration_seconds=duration,
        subject_id=subject_id
    )
    
    return jsonify({
        'success': True,
        'score': score,
        'total': total_questions,
        'percentage': round((score / total_questions) * 100, 2) if total_questions > 0 else 0,
        'result_id': str(result_id.inserted_id)
    })



@main_bp.route('/results')
@login_required
def results():
    subject_id = request.args.get('subject_id')
    user_results = ExamResult.get_user_results(current_user.id, subject_id)
    
    # Enrich results with subject names
    for res in user_results:
        if 'subject_id' in res and res['subject_id']:
            subject = Subject.get(res['subject_id'])
            if subject:
                res['subject_name'] = subject['name']
        else:
            res['subject_name'] = "Thủy văn công trình" # Default fallback
            
    subjects = Subject.get_all()
    return render_template('results.html', results=user_results, subjects=subjects, selected_subject_id=subject_id)

@main_bp.route('/result/<result_id>')
@login_required
def result_detail(result_id):
    try:
        result = mongo.db.exam_results.find_one({'_id': ObjectId(result_id), 'user_id': ObjectId(current_user.id)})
        if not result:
            flash('Không tìm thấy kết quả', 'error')
            return redirect(url_for('main.results'))
            
        if 'subject_id' in result and result['subject_id']:
            subject = Subject.get(result['subject_id'])
            if subject:
                result['subject_name'] = subject['name']
        
        return render_template('results_detail.html', result=result)
    except:
        flash('ID kết quả không hợp lệ', 'error')
        return redirect(url_for('main.results'))

@main_bp.route('/statistics')
@login_required
def statistics():
    subject_id = request.args.get('subject_id')
    user_results = ExamResult.get_user_results(current_user.id, subject_id)
    stats = ExamResult.get_user_stats(current_user.id, subject_id)
    
    subjects = Subject.get_all()
    
    # Generate chart if there are results
    chart_data = None
    if user_results:
        fig = Figure(figsize=(10, 6))
        ax = fig.subplots()
        
        # Get last 10 results or all if less than 10
        display_results = user_results[:10] if len(user_results) > 10 else user_results
        
        # Reverse to show oldest to newest
        display_results.reverse()
        
        dates = [r['completed_at'].strftime('%d/%m') for r in display_results]
        scores = [r['percentage'] for r in display_results]
        
        bars = ax.bar(range(len(dates)), scores, color=['#4CAF50' if s >= 50 else '#F44336' for s in scores])
        ax.set_xlabel('Lần thi')
        ax.set_ylabel('Điểm (%)')
        ax.set_title('Biểu đồ điểm thi 10 lần gần nhất' + (f' - {Subject.get(subject_id)["name"]}' if subject_id else ''))
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha='right')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}%', ha='center', va='bottom')
        
        # Save chart to base64
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=100)
        buf.seek(0)
        chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('Statistics.html', stats=stats, chart_data=chart_data, subjects=subjects, selected_subject_id=subject_id)

@main_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_questions():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này', 'error')
        return redirect(url_for('main.index'))
    
    subjects = Subject.get_all()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Không có file được chọn', 'error')
            return redirect(request.url)
        
        subject_id = request.form.get('subject_id')
        if not subject_id:
            flash('Vui lòng chọn môn học', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('Không có file được chọn', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.docx'):
            try:
                count = import_from_docx(file, subject_id)
                if count > 0:
                    flash(f'Đã import thành công {count} câu hỏi', 'success')
                else:
                    flash('Không tìm thấy câu hỏi nào trong file', 'warning')
            except Exception as e:
                flash(f'Lỗi khi import: {str(e)}', 'error')
        else:
            flash('Vui lòng chọn file Word (.docx)', 'error')
        
        return redirect(url_for('main.import_questions'))
    
    return render_template('import.html', subjects=subjects)

@main_bp.route('/manage-questions')
@login_required
def manage_questions():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này', 'error')
        return redirect(url_for('main.index'))
    
    subject_id = request.args.get('subject_id')
    
    if subject_id:
        questions = Question.get_by_subject(subject_id)
    else:
        questions = Question.get_all()
        
    subjects = Subject.get_all()
    subjects_dict = {str(s['_id']): s['name'] for s in subjects}
    
    for q in questions:
        # Create a serializable version for the JS edit modal
        q_json = q.copy()
        q_json['_id'] = str(q_json['_id'])
        if 'subject_id' in q_json:
            q_json['subject_id'] = str(q_json['subject_id'])
            
        q_json.pop('created_at', None)
        q_json.pop('updated_at', None)
        q['json_data'] = q_json
        
        # Add subject name for display
        if 'subject_id' in q:
            q['subject_name'] = subjects_dict.get(str(q['subject_id']), 'Không xác định')
        else:
            q['subject_name'] = 'Thủy văn công trình'
    
    categories = mongo.db.questions.distinct('category')
    
    return render_template('manage_questions.html', questions=questions, categories=categories, subjects=subjects, selected_subject_id=subject_id)

@main_bp.route('/api/questions/categories')
@login_required
def get_categories():
    categories = mongo.db.questions.distinct('category')
    return jsonify(categories)

@main_bp.route('/api/questions', methods=['POST'])
@main_bp.route('/api/questions/<question_id>', methods=['DELETE', 'PUT'])
@login_required
def manage_question_api(question_id=None):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        if request.method == 'POST':
            data = request.json
            new_question = {
                'question': data.get('question'),
                'options': data.get('options'),
                'correct_answer': data.get('correct_answer'),
                'category': data.get('category', 'Thủy văn công trình'),
                'difficulty': data.get('difficulty', 'medium'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            if data.get('subject_id'):
                new_question['subject_id'] = ObjectId(data.get('subject_id'))
            
            # Basic validation
            if not new_question['question'] or not new_question['options'] or not new_question['correct_answer']:
                return jsonify({'success': False, 'error': 'Thiếu thông tin câu hỏi'}), 400
                
            result = mongo.db.questions.insert_one(new_question)
            return jsonify({'success': True, 'id': str(result.inserted_id)})

        elif request.method == 'DELETE':
            result = mongo.db.questions.delete_one({'_id': ObjectId(question_id)})
            if result.deleted_count > 0:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Question not found'}), 404
        
        elif request.method == 'PUT':
            data = request.json
            update_data = {
                'question': data.get('question'),
                'options': data.get('options'),
                'correct_answer': data.get('correct_answer'),
                'category': data.get('category', 'Thủy văn công trình'),
                'difficulty': data.get('difficulty', 'medium'),
                'updated_at': datetime.utcnow()
            }
            
            if data.get('subject_id'):
                update_data['subject_id'] = ObjectId(data.get('subject_id'))
            
            # Basic validation
            if not update_data['question'] or not update_data['options'] or not update_data['correct_answer']:
                return jsonify({'success': False, 'error': 'Thiếu thông tin câu hỏi'}), 400
                
            result = mongo.db.questions.update_one(
                {'_id': ObjectId(question_id)},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Không có thay đổi hoặc không tìm thấy câu hỏi'}), 404
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@main_bp.route('/manage-users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này', 'error')
        return redirect(url_for('main.index'))
    
    users = User.get_all()
    return render_template('manage_users.html', users=users)

@main_bp.route('/api/users/<user_id>', methods=['PATCH', 'DELETE'])
@login_required
def manage_user_api(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if str(user_id) == str(current_user.id):
        return jsonify({'success': False, 'error': 'Bạn không thể tự thay đổi quyền hoặc xóa chính mình'}), 400

    try:
        if request.method == 'PATCH':
            data = request.json
            new_role = data.get('role')
            if new_role not in ['admin', 'user']:
                return jsonify({'success': False, 'error': 'Quyền không hợp lệ'}), 400
                
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'role': new_role}}
            )
            return jsonify({'success': True})
            
        elif request.method == 'DELETE':
            mongo.db.users.delete_one({'_id': ObjectId(user_id)})
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@main_bp.route('/manage-subjects')
@login_required
def manage_subjects():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này', 'error')
        return redirect(url_for('main.index'))
    
    subjects = Subject.get_all()
    
    # Enrich with question counts
    for subject in subjects:
        subject['_id'] = str(subject['_id'])
        subject['question_count'] = Subject.count_questions(subject['_id'])
        
    return render_template('manage_subjects.html', subjects=subjects)

@main_bp.route('/api/subjects', methods=['GET', 'POST'])
@login_required
def subjects_api():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        if request.method == 'GET':
            subjects = Subject.get_all()
            result = []
            for s in subjects:
                result.append({
                    'id': str(s['_id']),
                    'name': s['name'],
                    'description': s.get('description', '')
                })
            return jsonify(result)
            
        elif request.method == 'POST':
            data = request.json
            name = data.get('name')
            description = data.get('description', '')
            
            if not name:
                return jsonify({'success': False, 'error': 'Tên môn học là bắt buộc'}), 400
                
            result = Subject.create(name, description)
            return jsonify({'success': True, 'id': str(result.inserted_id)})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@main_bp.route('/api/subjects/<subject_id>', methods=['PUT', 'DELETE'])
@login_required
def subject_detail_api(subject_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        if request.method == 'PUT':
            data = request.json
            name = data.get('name')
            description = data.get('description', '')
            
            if not name:
                return jsonify({'success': False, 'error': 'Tên môn học là bắt buộc'}), 400
                
            Subject.update(subject_id, name, description)
            return jsonify({'success': True})
            
        elif request.method == 'DELETE':
            success, message = Subject.delete(subject_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': message}), 400
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@main_bp.route('/profile')
@login_required
def profile():
    stats = ExamResult.get_user_stats(current_user.id)
    user_data = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
    
    return render_template('profile.html', user=current_user, stats=stats, user_data=user_data)
