# -*- coding: utf-8 -*-
"""
Система безопасности и защиты от атак
Содержит защиту от DDoS, CSRF, XSS и другие меры безопасности
"""

from flask import Flask, request, jsonify, abort, g, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_caching import Cache
import redis
import structlog
import time
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta
import os

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Инициализация Redis для кэширования и rate limiting
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=int(os.environ.get('REDIS_DB', 0)),
    decode_responses=True
)

# Инициализация кэша
cache = Cache()

# Инициализация rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', 6379)}",
    default_limits=["1000 per hour", "100 per minute"]
)

# Инициализация Talisman для безопасности
talisman = Talisman()

class SecurityManager:
    """Менеджер безопасности"""
    
    def __init__(self, app=None):
        self.app = app
        self.suspicious_ips = set()
        self.blocked_ips = set()
        self.rate_limit_cache = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализирует систему безопасности"""
        self.app = app
        
        # Настройка Talisman
        talisman.init_app(
            app,
            force_https=app.config.get('FORCE_HTTPS', False),
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy={
                'default-src': "'self'",
                'script-src': [
                    "'self'",
                    "'unsafe-inline'",
                    'https://cdnjs.cloudflare.com',
                    'https://cdn.jsdelivr.net'
                ],
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",
                    'https://cdnjs.cloudflare.com',
                    'https://fonts.googleapis.com'
                ],
                'font-src': [
                    "'self'",
                    'https://fonts.gstatic.com',
                    'https://cdnjs.cloudflare.com'
                ],
                'img-src': [
                    "'self'",
                    'data:',
                    'https:'
                ],
                'connect-src': [
                    "'self'",
                    'wss:',
                    'ws:'
                ]
            }
        )
        
        # Настройка rate limiting
        limiter.init_app(app)
        
        # Настройка кэширования
        cache.init_app(app, config={
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', 6379)}"
        })
        
        # Регистрация обработчиков
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Настройка логирования
        app.logger.setLevel('INFO')
    
    def before_request(self):
        """Обработчик перед запросом"""
        # Проверка IP на блокировку
        client_ip = get_remote_address()
        if client_ip in self.blocked_ips:
            logger.warning("Blocked IP attempted access", ip=client_ip)
            abort(403)
        
        # Проверка на подозрительную активность
        if self.is_suspicious_request():
            self.handle_suspicious_request()
        
        # Логирование запроса
        g.start_time = time.time()
        logger.info("Request started", 
                   method=request.method, 
                   path=request.path, 
                   ip=client_ip,
                   user_agent=request.headers.get('User-Agent', ''))
    
    def after_request(self, response):
        """Обработчик после запроса"""
        # Логирование времени выполнения
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info("Request completed", 
                       status=response.status_code,
                       duration=duration)
            
            # Предупреждение о медленных запросах
            if duration > 5.0:
                logger.warning("Slow request detected", 
                              path=request.path, 
                              duration=duration)
        
        # Добавление заголовков безопасности
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def is_suspicious_request(self):
        """Проверяет подозрительность запроса"""
        client_ip = get_remote_address()
        
        # Проверка User-Agent
        user_agent = request.headers.get('User-Agent', '').lower()
        suspicious_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'go-http-client', 'java/', 'okhttp'
        ]
        
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        # Проверка на SQL инъекции в параметрах
        suspicious_patterns = [
            'union select', 'drop table', 'delete from', 'insert into',
            'update set', 'script>', '<script', 'javascript:', 'onload=',
            'onerror=', 'onclick=', 'eval(', 'alert(', 'document.cookie'
        ]
        
        query_string = str(request.query_string).lower()
        if any(pattern in query_string for pattern in suspicious_patterns):
            return True
        
        # Проверка на частые запросы
        if self.is_rate_limited(client_ip):
            return True
        
        return False
    
    def handle_suspicious_request(self):
        """Обрабатывает подозрительный запрос"""
        client_ip = get_remote_address()
        
        # Добавляем IP в список подозрительных
        self.suspicious_ips.add(client_ip)
        
        # Логируем подозрительную активность
        logger.warning("Suspicious request detected", 
                      ip=client_ip,
                      path=request.path,
                      user_agent=request.headers.get('User-Agent', ''))
        
        # Если слишком много подозрительных запросов - блокируем
        if self.get_suspicious_count(client_ip) > 10:
            self.block_ip(client_ip)
            logger.error("IP blocked due to suspicious activity", ip=client_ip)
    
    def is_rate_limited(self, ip):
        """Проверяет превышение лимита запросов"""
        current_time = time.time()
        window = 60  # 1 минута
        
        # Получаем историю запросов для IP
        key = f"rate_limit:{ip}"
        requests = redis_client.lrange(key, 0, -1)
        
        # Удаляем старые запросы
        cutoff = current_time - window
        requests = [float(r) for r in requests if float(r) > cutoff]
        
        # Проверяем лимит (100 запросов в минуту)
        if len(requests) > 100:
            return True
        
        # Добавляем текущий запрос
        requests.append(current_time)
        redis_client.delete(key)
        if requests:
            redis_client.rpush(key, *requests)
            redis_client.expire(key, window)
        
        return False
    
    def get_suspicious_count(self, ip):
        """Получает количество подозрительных запросов от IP"""
        key = f"suspicious:{ip}"
        return redis_client.get(key) or 0
    
    def block_ip(self, ip):
        """Блокирует IP адрес"""
        self.blocked_ips.add(ip)
        key = f"blocked:{ip}"
        redis_client.set(key, "1", ex=3600)  # Блокировка на 1 час
        logger.error("IP blocked", ip=ip)
    
    def unblock_ip(self, ip):
        """Разблокирует IP адрес"""
        self.blocked_ips.discard(ip)
        key = f"blocked:{ip}"
        redis_client.delete(key)
        logger.info("IP unblocked", ip=ip)

# Декораторы безопасности
def require_auth(f):
    """Декоратор для проверки аутентификации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user') or not g.user:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_premium(f):
    """Декоратор для проверки премиум статуса"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user') or not g.user or not g.user.is_premium:
            return jsonify({'error': 'Premium subscription required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_by_user(f):
    """Декоратор для ограничения по пользователю"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(g, 'user') and g.user:
            user_id = g.user.id
            key = f"user_rate:{user_id}"
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, 60)  # 1 минута
            if current > 50:  # 50 запросов в минуту на пользователя
                return jsonify({'error': 'Rate limit exceeded'}), 429
        return f(*args, **kwargs)
    return decorated_function

def cache_response(timeout=300):
    """Декоратор для кэширования ответов"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Создаем ключ кэша на основе функции и аргументов
            cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Проверяем кэш
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кэшируем результат
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        return decorated_function
    return decorator

# Функции для защиты от атак
def sanitize_input(data):
    """Очищает пользовательский ввод"""
    if isinstance(data, str):
        # Удаляем потенциально опасные символы
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', 'script', 'javascript']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()
    return data

def validate_csrf_token(token):
    """Валидирует CSRF токен"""
    if not token:
        return False
    
    # Проверяем токен в сессии
    session_token = session.get('csrf_token')
    if not session_token:
        return False
    
    return secrets.compare_digest(token, session_token)

def generate_csrf_token():
    """Генерирует CSRF токен"""
    token = secrets.token_hex(32)
    session['csrf_token'] = token
    return token

def hash_password(password):
    """Хеширует пароль с солью"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password, password_hash):
    """Проверяет пароль"""
    try:
        salt, hash_part = password_hash.split(':')
        password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(hash_part, password_hash_check.hex())
    except ValueError:
        return False

# Мониторинг и алерты
class SecurityMonitor:
    """Монитор безопасности"""
    
    def __init__(self):
        self.alert_thresholds = {
            'failed_logins': 5,  # 5 неудачных попыток входа
            'suspicious_requests': 10,  # 10 подозрительных запросов
            'rate_limit_hits': 20,  # 20 превышений лимита
        }
    
    def check_alerts(self):
        """Проверяет условия для алертов"""
        alerts = []
        
        # Проверяем неудачные попытки входа
        failed_logins = redis_client.get('failed_logins') or 0
        if int(failed_logins) > self.alert_thresholds['failed_logins']:
            alerts.append({
                'type': 'failed_logins',
                'message': f'High number of failed login attempts: {failed_logins}',
                'severity': 'high'
            })
        
        # Проверяем подозрительные запросы
        suspicious_requests = redis_client.get('suspicious_requests') or 0
        if int(suspicious_requests) > self.alert_thresholds['suspicious_requests']:
            alerts.append({
                'type': 'suspicious_requests',
                'message': f'High number of suspicious requests: {suspicious_requests}',
                'severity': 'medium'
            })
        
        return alerts
    
    def send_alert(self, alert):
        """Отправляет алерт"""
        logger.error("Security alert", 
                    type=alert['type'],
                    message=alert['message'],
                    severity=alert['severity'])

# Инициализация системы безопасности
security_manager = SecurityManager()
security_monitor = SecurityMonitor()

def init_security(app):
    """Инициализирует систему безопасности"""
    security_manager.init_app(app)
    
    # Настройка дополнительных заголовков безопасности
    @app.after_request
    def security_headers(response):
        response.headers['Server'] = 'Golan-Auction/1.0'
        response.headers['X-Powered-By'] = 'Flask'
        return response
    
    # Обработка ошибок
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Access forbidden'}), 403
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error", error=str(error))
        return jsonify({'error': 'Internal server error'}), 500
