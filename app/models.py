from datetime import datetime
from flask_login import UserMixin
from app import mongo
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.role = user_data.get('role', 'user')
    
    @staticmethod
    def get(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except:
            pass
        return None
    
    @staticmethod
    def get_by_username(username):
        user_data = mongo.db.users.find_one({'username': username})
        if user_data:
            return User(user_data)
        return None
    
    @staticmethod
    def get_all():
        return list(mongo.db.users.find())

class Subject:
    @staticmethod
    def create(name, description=""):
        return mongo.db.subjects.insert_one({
            'name': name,
            'description': description,
            'created_at': datetime.utcnow()
        })
    
    @staticmethod
    def get_all():
        return list(mongo.db.subjects.find({}, sort=[('name', 1)]))
    
    @staticmethod
    def get(subject_id):
        try:
            return mongo.db.subjects.find_one({'_id': ObjectId(subject_id)})
        except:
            return None
            
    @staticmethod
    def update(subject_id, name, description=""):
        return mongo.db.subjects.update_one(
            {'_id': ObjectId(subject_id)},
            {'$set': {'name': name, 'description': description, 'updated_at': datetime.utcnow()}}
        )
        
    @staticmethod
    def delete(subject_id):
        # Check if there are questions for this subject
        count = mongo.db.questions.count_documents({'subject_id': ObjectId(subject_id)})
        if count > 0:
            return False, f"Không thể xóa môn học này vì đang có {count} câu hỏi."
            
        mongo.db.subjects.delete_one({'_id': ObjectId(subject_id)})
        return True, ""
        
    @staticmethod
    def count_questions(subject_id):
        return mongo.db.questions.count_documents({'subject_id': ObjectId(subject_id)})

class Question:
    @staticmethod
    def create(question_text, options, correct_answer, category, difficulty, subject_id=None):
        data = {
            'question': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'category': category,
            'difficulty': difficulty,
            'created_at': datetime.utcnow()
        }
        
        if subject_id:
            data['subject_id'] = ObjectId(subject_id)
            
        return mongo.db.questions.insert_one(data)
    
    @staticmethod
    def get_all():
        return list(mongo.db.questions.find())
        
    @staticmethod
    def get_by_subject(subject_id):
        return list(mongo.db.questions.find({'subject_id': ObjectId(subject_id)}))
    
    @staticmethod
    def get_by_category(category):
        return list(mongo.db.questions.find({'category': category}))
    
    @staticmethod
    def get_random_questions(limit=20, subject_id=None):
        pipeline = []
        if subject_id:
            pipeline.append({'$match': {'subject_id': ObjectId(subject_id)}})
            
        pipeline.append({'$sample': {'size': limit}})
        return list(mongo.db.questions.aggregate(pipeline))
    
    @staticmethod
    def count(subject_id=None):
        query = {}
        if subject_id:
            query['subject_id'] = ObjectId(subject_id)
        return mongo.db.questions.count_documents(query)

class ExamResult:
    @staticmethod
    def create(user_id, score, total_questions, answers, duration_seconds, subject_id=None):
        data = {
            'user_id': ObjectId(user_id),
            'score': score,
            'total_questions': total_questions,
            'percentage': (score / total_questions) * 100 if total_questions > 0 else 0,
            'answers': answers,
            'duration_seconds': duration_seconds,
            'completed_at': datetime.utcnow()
        }
        
        if subject_id:
            data['subject_id'] = ObjectId(subject_id)
            
        return mongo.db.exam_results.insert_one(data)
    
    @staticmethod
    def get_user_results(user_id, subject_id=None):
        query = {'user_id': ObjectId(user_id)}
        if subject_id:
            try:
                query['subject_id'] = ObjectId(subject_id)
            except:
                pass # Invalid subject_id, simpler to just ignore it or return empty
                
        return list(mongo.db.exam_results.find(
            query,
            sort=[('completed_at', -1)]
        ))
    
    @staticmethod
    def get_all_results():
        return list(mongo.db.exam_results.find())
    
    @staticmethod
    def get_user_stats(user_id, subject_id=None):
        results = ExamResult.get_user_results(user_id, subject_id)
        if not results:
            return None
        
        total_exams = len(results)
        average_score = sum(r['percentage'] for r in results) / total_exams if total_exams > 0 else 0
        best_score = max(r['percentage'] for r in results)
        worst_score = min(r['percentage'] for r in results)
        total_time = sum(r['duration_seconds'] for r in results)
        
        return {
            'total_exams': total_exams,
            'average_score': average_score,
            'best_score': best_score,
            'worst_score': worst_score,
            'total_time': total_time,
            'last_10_scores': [r['percentage'] for r in results[:10]]
        }
