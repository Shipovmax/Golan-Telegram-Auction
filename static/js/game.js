// Простой JavaScript для игры в голландский аукцион
document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы DOM
    const startGameBtn = document.getElementById('startGame');
    const nextRoundBtn = document.getElementById('nextRound');
    const resetGameBtn = document.getElementById('resetGame');
    const gameStatusEl = document.getElementById('gameStatus');
    const gameRoundEl = document.getElementById('gameRound');
    const currentLotEl = document.getElementById('currentLot');
    const bidsListEl = document.getElementById('bidsList');
    const auctionResultEl = document.getElementById('auctionResult');
    const playersListEl = document.getElementById('playersList');
    const userInfoEl = document.getElementById('userInfo');
    
    // Состояние игры
    let gameState = {
        game: { status: 'waiting', round: 0, current_lot: null },
        players: [],
        products: []
    };
    
    let userData = null;
    
    // Простые API функции
    async function apiCall(url, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return await response.json();
    }
    
    // Форматирование денег
    function formatMoney(amount) {
        return new Intl.NumberFormat('ru-RU').format(amount) + ' ₽';
    }
    
    // Показать уведомление
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            z-index: 1000;
            font-weight: bold;
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Загружает состояние игры
    async function loadGameState() {
        try {
            const response = await apiCall('/api/game/status');
            gameState = response;
            updateUI();
            
            // Загружаем данные пользователя
            await loadUserData();
            
        } catch (error) {
            console.error('Ошибка загрузки состояния игры:', error);
            showNotification('Ошибка загрузки состояния игры', 'error');
        }
    }
    
    // Загружает данные пользователя
    async function loadUserData() {
        try {
            const response = await apiCall('/api/user/data');
            if (response.success) {
                userData = response.user_data;
                updateUserInfo();
            }
        } catch (error) {
            console.log('Пользователь не найден');
        }
    }
    
    // Обновляет интерфейс
    function updateUI() {
        // Обновляем статус игры
        if (gameState.game) {
            gameStatusEl.textContent = getStatusText(gameState.game.status);
            gameRoundEl.textContent = `Раунд: ${gameState.game.current_round || 0}`;
        }
        
        // Обновляем кнопки
        updateButtons();
        
        // Обновляем текущий лот
        updateCurrentLot();
        
        // Обновляем список игроков
        updatePlayersList();
        
        // Обновляем информацию о пользователе
        updateUserInfo();
    }
    
    // Обновляет информацию о пользователе
    function updateUserInfo() {
        if (userData && userInfoEl) {
            userInfoEl.innerHTML = `
                <div class="user-card" style="
                    background: #f8fafc;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                ">
                    <h3 style="margin: 0 0 16px 0; color: #1a202c; font-size: 16px; font-weight: 600;">👤 Ваш профиль</h3>
                    <div class="user-stats" style="display: grid; gap: 8px;">
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Баланс:</span>
                            <span style="color: #10b981; font-weight: 600; font-size: 14px;">${formatMoney(userData.balance)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Прибыль:</span>
                            <span style="color: ${userData.total_profit >= 0 ? '#10b981' : '#ef4444'}; font-weight: 600; font-size: 14px;">${userData.total_profit >= 0 ? '+' : ''}${formatMoney(userData.total_profit)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Покупки:</span>
                            <span style="color: #f59e0b; font-weight: 600; font-size: 14px;">${userData.purchases}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Любимый:</span>
                            <span style="color: #8b5cf6; font-weight: 600; font-size: 14px;">${userData.wants}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Не любит:</span>
                            <span style="color: #ef4444; font-weight: 600; font-size: 14px;">${userData.no_wants}</span>
                        </div>
                    </div>
                </div>
            `;
        } else if (userInfoEl) {
            userInfoEl.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #6b7280;">
                    <p style="font-size: 14px;">Начните игру, чтобы увидеть ваш профиль</p>
                </div>
            `;
        }
    }
    
    // Возвращает текстовое описание статуса
    function getStatusText(status) {
        const statusMap = {
            'waiting': 'Ожидание начала',
            'playing': 'Игра идет',
            'finished': 'Игра завершена'
        };
        return statusMap[status] || 'Неизвестный статус';
    }
    
    // Обновляет состояние кнопок
    function updateButtons() {
        const isPlaying = gameState.game && gameState.game.status === 'playing';
        const isFinished = gameState.game && gameState.game.status === 'finished';
        
        startGameBtn.disabled = isPlaying;
        nextRoundBtn.disabled = !isPlaying || isFinished;
        resetGameBtn.disabled = false;
    }
    
    // Обновляет отображение текущего лота
    function updateCurrentLot() {
        if (gameState.game && gameState.game.current_lot) {
            const lot = gameState.game.current_lot;
            const canBuy = userData && userData.balance >= lot.current_price;
            
            currentLotEl.innerHTML = `
                <div class="lot-info" style="
                    background: #f8fafc;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                ">
                    <h3 style="margin: 0 0 16px 0; color: #1a202c; font-size: 18px; font-weight: 600;">${lot.name}</h3>
                    <div class="lot-details" style="display: grid; gap: 8px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Количество:</span> 
                            <span style="color: #3b82f6; font-weight: 600; font-size: 14px;">${lot.quantity} шт.</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Текущая цена:</span> 
                            <span style="color: #10b981; font-weight: 600; font-size: 16px;">${formatMoney(lot.current_price)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Себестоимость:</span> 
                            <span style="color: #f59e0b; font-weight: 600; font-size: 14px;">${formatMoney(lot.cost)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                            <span style="color: #6b7280; font-size: 14px;">Потенциальная прибыль:</span> 
                            <span style="color: #8b5cf6; font-weight: 600; font-size: 14px;">${formatMoney(lot.cost - lot.current_price)}</span>
                        </div>
                    </div>
                    ${userData ? `
                        <div class="user-actions" style="text-align: center;">
                            <button onclick="buyProduct(${lot.id})" 
                                    style="
                                        background: ${canBuy ? '#10b981' : '#d1d5db'};
                                        color: white;
                                        border: none;
                                        padding: 12px 24px;
                                        font-size: 14px;
                                        font-weight: 600;
                                        border-radius: 8px;
                                        cursor: ${canBuy ? 'pointer' : 'not-allowed'};
                                        transition: all 0.2s;
                                        min-width: 160px;
                                    "
                                    onmouseover="if(this.style.cursor === 'pointer') this.style.background = '#059669'"
                                    onmouseout="this.style.background = '${canBuy ? '#10b981' : '#d1d5db'}'"
                                    ${!canBuy ? 'disabled' : ''}>
                                ${canBuy ? '🛒 Купить за ' + formatMoney(lot.current_price) : '❌ Недостаточно средств'}
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        } else {
            currentLotEl.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #6b7280;">
                    <h3 style="color: #374151; font-size: 16px; margin-bottom: 8px;">💎 Товар не выбран</h3>
                    <p style="font-size: 14px;">Нажмите "Следующий раунд" чтобы начать торги</p>
                </div>
            `;
        }
    }
    
    // Обновляет список игроков
    function updatePlayersList() {
        if (gameState.players && gameState.players.length > 0) {
            playersListEl.innerHTML = gameState.players.map(player => `
                <div class="player-card" style="
                    background: rgba(255, 255, 255, 0.9);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    min-width: 150px;
                ">
                    <div class="player-avatar" style="
                        width: 40px;
                        height: 40px;
                        background: #2196F3;
                        color: white;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 18px;
                        margin: 0 auto 10px;
                    ">${player.name.charAt(0)}</div>
                    <h3 style="margin: 0 0 10px 0; color: #333;">${player.name}</h3>
                    <div style="font-size: 14px; color: #666;">
                        <p style="margin: 5px 0;"><strong>Баланс:</strong> ${formatMoney(player.balance)}</p>
                        <p style="margin: 5px 0;"><strong>Прибыль:</strong> <span style="color: ${player.total_profit >= 0 ? '#10b981' : '#ef4444'};">${player.total_profit >= 0 ? '+' : ''}${formatMoney(player.total_profit)}</span></p>
                        <p style="margin: 5px 0;"><strong>Покупки:</strong> ${player.purchases}</p>
                    </div>
                </div>
            `).join('');
        } else {
            playersListEl.innerHTML = '<p style="text-align: center; color: #666;">Загрузка игроков...</p>';
        }
    }
    
    // Начинает новую игру
    async function startGame() {
        try {
            const response = await apiCall('/api/game/start', 'POST');
            
            if (response.success) {
                showNotification('Игра начата!', 'success');
                if (response.user_data) {
                    userData = response.user_data;
                }
                await loadGameState();
            } else {
                showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка запуска игры:', error);
            showNotification('Ошибка запуска игры', 'error');
        }
    }
    
    // Покупает товар
    async function buyProduct(productId) {
        try {
            const response = await apiCall('/api/user/buy', 'POST', { product_id: productId });
            
            if (response.success) {
                showNotification(response.message, 'success');
                userData = response.user_data;
                await loadGameState();
            } else {
                showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка покупки товара:', error);
            showNotification('Ошибка покупки товара', 'error');
        }
    }
    
    // Делаем функцию покупки глобальной
    window.buyProduct = buyProduct;
    
    // Переходит к следующему раунду
    async function nextRound() {
        try {
            const response = await apiCall('/api/game/next-round', 'POST');
            
            if (response.success) {
                // Обновляем состояние игры
                if (gameState.game) {
                    gameState.game.round = response.round;
                    gameState.game.current_lot = response.current_lot;
                }
                
                if (response.game_over) {
                    gameState.game.status = 'finished';
                    showNotification(response.message, 'info');
                }
                
                updateUI();
                
                // Показываем результат раунда
                if (response.winner) {
                    auctionResultEl.innerHTML = `
                        <div style="
                            background: #f0fdf4;
                            padding: 20px;
                            border-radius: 8px;
                            border: 1px solid #bbf7d0;
                            text-align: center;
                        ">
                            <h3 style="color: #10b981; margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">🏆 ${response.winner.name} купил!</h3>
                            <div style="display: grid; gap: 8px; text-align: left; max-width: 300px; margin: 0 auto;">
                                <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                                    <span style="color: #6b7280; font-size: 14px;">Товар:</span>
                                    <span style="color: #1a202c; font-weight: 600; font-size: 14px;">${response.current_lot.name}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                                    <span style="color: #6b7280; font-size: 14px;">Цена:</span>
                                    <span style="color: #10b981; font-weight: 600; font-size: 14px;">${formatMoney(response.winner.purchase_price)}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                                    <span style="color: #6b7280; font-size: 14px;">Прибыль:</span>
                                    <span style="color: ${response.winner.profit >= 0 ? '#10b981' : '#ef4444'}; font-weight: 600; font-size: 14px;">${response.winner.profit >= 0 ? '+' : ''}${formatMoney(response.winner.profit)}</span>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    auctionResultEl.innerHTML = `
                        <div style="
                            background: #fef3c7;
                            padding: 20px;
                            border-radius: 8px;
                            border: 1px solid #fde68a;
                            text-align: center;
                        ">
                            <h3 style="color: #f59e0b; margin: 0 0 8px 0; font-size: 16px; font-weight: 600;">⏳ Товар не продан</h3>
                            <p style="color: #6b7280; font-size: 14px; margin: 0;">Цена снижена до ${formatMoney(response.current_lot.current_price)}</p>
                        </div>
                    `;
                }
                
            } else {
                showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка проведения раунда:', error);
            showNotification('Ошибка проведения раунда', 'error');
        }
    }
    
    // Сбрасывает игру
    async function resetGame() {
        try {
            const response = await apiCall('/api/game/reset', 'POST');
            
            if (response.success) {
                showNotification('Игра сброшена!', 'success');
                await loadGameState();
            } else {
                showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка сброса игры:', error);
            showNotification('Ошибка сброса игры', 'error');
        }
    }
    
    // Обработчики событий
    startGameBtn.addEventListener('click', startGame);
    nextRoundBtn.addEventListener('click', nextRound);
    resetGameBtn.addEventListener('click', resetGame);
    
    // Загружаем начальное состояние
    loadGameState();
    
    // Обновляем состояние каждые 3 секунды
    setInterval(loadGameState, 3000);
});