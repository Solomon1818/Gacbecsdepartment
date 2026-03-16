from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
import bcrypt
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user, hashed_pw = User.get_by_username(username)

        if user and hashed_pw and bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
