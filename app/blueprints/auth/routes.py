from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from . import auth_bp
from ...extensions import db, login_manager
from ...models import User
from ...security import hash_password, verify_password

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and verify_password(user.password_hash, password):
            login_user(user, remember=bool(request.form.get('remember')))
            return redirect(url_for('core.dashboard'))
        flash('Email o contraseña inválida', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    from config import Config
    if not Config.ALLOW_REGISTRATION and User.query.count() > 0:
        flash('Registro deshabilitado. Contacta al administrador.', 'warning')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Usuario ya existe', 'warning')
            return redirect(url_for('auth.register'))
        u = User(email=email, name=name, password_hash=hash_password(password))
        if User.query.count() == 0:
            u.is_admin = True
        db.session.add(u)
        db.session.commit()
        flash('Usuario registrado. Inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
