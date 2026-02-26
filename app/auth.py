from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from datetime import datetime
from app import mongo
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = mongo.db.users.find_one({'username': username})
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            user = User(user_data)
            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự', 'error')
            return render_template('register.html')
        
        # Check if user exists
        if mongo.db.users.find_one({'username': username}):
            flash('Tên đăng nhập đã tồn tại', 'error')
            return render_template('register.html')
        
        if mongo.db.users.find_one({'email': email}):
            flash('Email đã được sử dụng', 'error')
            return render_template('register.html')
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        mongo.db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': 'user',
            'created_at': datetime.utcnow()
        })
        
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công', 'success')
    return redirect(url_for('auth.login'))
