from app import create_app, mongo
from app.models import Subject
from bson import ObjectId

app = create_app()

with app.app_context():
    print("Starting migration...")
    
    # 1. Create default subject if not exists
    default_subject_name = "Thủy văn công trình"
    default_subject = mongo.db.subjects.find_one({'name': default_subject_name})
    
    if not default_subject:
        print(f"Creating default subject: {default_subject_name}")
        result = Subject.create(
            name=default_subject_name,
            description="Môn học mặc định"
        )
        subject_id = result.inserted_id
    else:
        print(f"Default subject already exists: {default_subject_name}")
        subject_id = default_subject['_id']
        
    print(f"Subject ID: {subject_id}")
    
    # 2. Update existing questions without subject_id
    print("Updating questions...")
    result = mongo.db.questions.update_many(
        {'subject_id': {'$exists': False}},
        {'$set': {'subject_id': ObjectId(subject_id)}}
    )
    print(f"Updated {result.modified_count} questions.")
    
    # 3. Update existing exam results without subject_id
    print("Updating exam results...")
    result = mongo.db.exam_results.update_many(
        {'subject_id': {'$exists': False}},
        {'$set': {'subject_id': ObjectId(subject_id)}}
    )
    print(f"Updated {result.modified_count} exam results.")
    
    print("Migration completed successfully!")
