// Основной JavaScript файл для веб-приложения аукциона
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация приложения
    console.log('Golan Auction App загружен');
    
    // Добавляем анимации для карточек при наведении
    const cards = document.querySelectorAll('.feature-card, .player-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Плавная прокрутка для навигации
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
});

// Утилиты для работы с API
const API = {
    baseURL: '',
    
    /**
     * Выполняет запрос к API
     * @param {string} endpoint - URL endpoint
     * @param {Object} options - Опции запроса
     * @returns {Promise} - Промис с результатом запроса
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Ошибка запроса');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    /**
     * GET запрос к API
     * @param {string} endpoint - URL endpoint
     * @returns {Promise} - Промис с результатом
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    /**
     * POST запрос к API
     * @param {string} endpoint - URL endpoint
     * @param {Object} data - Данные для отправки
     * @returns {Promise} - Промис с результатом
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

// Утилиты для форматирования
const Utils = {
    /**
     * Форматирует число как денежную сумму
     * @param {number} amount - Сумма
     * @returns {string} - Отформатированная строка
     */
    formatMoney(amount) {
        return new Intl.NumberFormat('ru-RU').format(amount) + ' ₽';
    },
    
    /**
     * Форматирует число с разделителями
     * @param {number} number - Число
     * @returns {string} - Отформатированная строка
     */
    formatNumber(number) {
        return new Intl.NumberFormat('ru-RU').format(number);
    },
    
    /**
     * Показывает уведомление пользователю
     * @param {string} message - Сообщение
     * @param {string} type - Тип уведомления (success, error, info)
     */
    showNotification(message, type = 'info') {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? '#4facfe' : type === 'error' ? '#f5576c' : '#667eea'};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            z-index: 3000;
            animation: slideIn 0.3s ease;
        `;
        
        // Добавляем анимацию
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        
        // Добавляем в DOM
        document.body.appendChild(notification);
        
        // Удаляем через 3 секунды
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => {
                document.body.removeChild(notification);
                document.head.removeChild(style);
            }, 300);
        }, 3000);
    },
    
    /**
     * Показывает модальное окно загрузки
     * @param {boolean} show - Показать или скрыть
     */
    showLoading(show = true) {
        const modal = document.getElementById('loadingModal');
        if (modal) {
            modal.style.display = show ? 'block' : 'none';
        }
    }
};

// Экспортируем утилиты для использования в других файлах
window.API = API;
window.Utils = Utils;
