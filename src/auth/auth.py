# -*- coding: utf-8 -*-
"""
Система аутентификации и авторизации
Содержит модели пользователей, формы и функции безопасности
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import re
from ..models.database import db

# Создаем Blueprint для аутентификации
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Инициализируем Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

class User(UserMixin, db.Model):
    """Модель пользователя с расширенными возможностями"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    total_games_played = db.Column(db.Integer, default=0)
    total_profit = db.Column(db.Integer, default=0)
    best_game_profit = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    
    # Связи
    game_sessions = db.relationship('UserGameSession', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Устанавливает хешированный пароль"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверяет пароль"""
        return check_password_hash(self.password_hash, password)
    
    def update_login_stats(self):
        """Обновляет статистику входа"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
    
    def add_experience(self, points):
        """Добавляет опыт и проверяет повышение уровня"""
        self.experience += points
        # Каждый уровень требует 1000 опыта
        new_level = (self.experience // 1000) + 1
        if new_level > self.level:
            self.level = new_level
            return True  # Уровень повышен
        return False
    
    def to_dict(self):
        """Преобразует пользователя в словарь"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'avatar_url': self.avatar_url,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'total_games_played': self.total_games_played,
            'total_profit': self.total_profit,
            'best_game_profit': self.best_game_profit,
            'level': self.level,
            'experience': self.experience
        }

class UserGameSession(db.Model):
    """Модель игровой сессии пользователя"""
    __tablename__ = 'user_game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    player_data = db.Column(db.JSON, nullable=True)  # Данные игрока в сессии
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    final_profit = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

class UserAchievement(db.Model):
    """Модель достижений пользователя"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_type = db.Column(db.String(50), nullable=False)
    achievement_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer, default=0)

# Формы
class LoginForm(FlaskForm):
    """Форма входа"""
    username = StringField('Имя пользователя или Email', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegisterForm(FlaskForm):
    """Форма регистрации"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(), 
        Length(min=3, max=20, message='Имя пользователя должно быть от 3 до 20 символов')
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    password = PasswordField('Пароль', validators=[
        DataRequired(), 
        Length(min=8, message='Пароль должен содержать минимум 8 символов')
    ])
    password2 = PasswordField('Подтвердите пароль', validators=[
        DataRequired(), 
        EqualTo('password', message='Пароли не совпадают')
    ])
    agree_terms = BooleanField('Я согласен с условиями использования', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        """Валидация имени пользователя"""
        if not re.match(r'^[a-zA-Z0-9_]+$', username.data):
            raise ValidationError('Имя пользователя может содержать только буквы, цифры и подчеркивания')
        
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято')
    
    def validate_email(self, email):
        """Валидация email"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')
    
    def validate_password(self, password):
        """Валидация пароля"""
        if not re.search(r'[A-Z]', password.data):
            raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву')
        if not re.search(r'[a-z]', password.data):
            raise ValidationError('Пароль должен содержать хотя бы одну строчную букву')
        if not re.search(r'\d', password.data):
            raise ValidationError('Пароль должен содержать хотя бы одну цифру')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password.data):
            raise ValidationError('Пароль должен содержать хотя бы один специальный символ')

class ProfileForm(FlaskForm):
    """Форма редактирования профиля"""
    first_name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    avatar_url = StringField('URL аватара', validators=[Length(max=255)])
    submit = SubmitField('Сохранить изменения')

# Функции аутентификации
@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID"""
    return User.query.get(int(user_id))

def create_user(username, email, password, first_name, last_name):
    """Создает нового пользователя"""
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

def authenticate_user(username_or_email, password):
    """Аутентифицирует пользователя"""
    # Ищем пользователя по имени или email
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if user and user.check_password(password) and user.is_active:
        user.update_login_stats()
        return user
    return None

# Маршруты аутентификации
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.username.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            flash('Добро пожаловать!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            login_user(user)
            flash('Регистрация успешна! Добро пожаловать!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash('Ошибка при регистрации. Попробуйте еще раз.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Страница профиля"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Редактирование профиля"""
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        current_user.avatar_url = form.avatar_url.data
        db.session.commit()
        flash('Профиль обновлен!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)

# API endpoints для аутентификации
@auth_bp.route('/api/check-auth')
def check_auth():
    """API для проверки аутентификации"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    return jsonify({'authenticated': False})

@auth_bp.route('/api/user-stats')
@login_required
def user_stats():
    """API для получения статистики пользователя"""
    return jsonify({
        'total_games': current_user.total_games_played,
        'total_profit': current_user.total_profit,
        'best_profit': current_user.best_game_profit,
        'level': current_user.level,
        'experience': current_user.experience,
        'login_count': current_user.login_count
    })

def init_auth(app):
    """Инициализирует систему аутентификации"""
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    
    # Создаем таблицы
    with app.app_context():
        db.create_all()
