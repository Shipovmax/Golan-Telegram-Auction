// JavaScript для страницы игры с поддержкой пользователя
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
    const buyButtonEl = document.getElementById('buyButton');
    
    // Состояние игры
    let gameState = {
        status: 'waiting',
        round: 0,
        currentLot: null,
        bids: {},
        players: []
    };
    
    // Данные пользователя
    let userData = null;
    
    /**
     * Загружает текущее состояние игры с сервера
     */
    async function loadGameState() {
        try {
            Utils.showLoading(true);
            const response = await API.get('/api/game/status');
            
            gameState = response;
            updateUI();
            
            // Загружаем данные пользователя
            await loadUserData();
            
        } catch (error) {
            console.error('Ошибка загрузки состояния игры:', error);
            Utils.showNotification('Ошибка загрузки состояния игры', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }
    
    /**
     * Загружает данные пользователя
     */
    async function loadUserData() {
        try {
            const response = await API.get('/api/user/data');
            if (response.success) {
                userData = response.user_data;
                updateUserInfo();
            }
        } catch (error) {
            console.log('Пользователь не найден или сессия не активна');
        }
    }
    
    /**
     * Обновляет интерфейс на основе текущего состояния игры
     */
    function updateUI() {
        // Обновляем статус игры
        gameStatusEl.textContent = getStatusText(gameState.game.status);
        gameRoundEl.textContent = `Раунд: ${gameState.game.round}`;
        
        // Обновляем кнопки
        updateButtons();
        
        // Обновляем текущий лот
        updateCurrentLot();
        
        // Обновляем список игроков
        updatePlayersList();
        
        // Обновляем ставки и результат
        updateBidsAndResult();
        
        // Обновляем информацию о пользователе
        updateUserInfo();
    }
    
    /**
     * Обновляет информацию о пользователе
     */
    function updateUserInfo() {
        if (userData && userInfoEl) {
            userInfoEl.innerHTML = `
                <div class="user-card">
                    <h3>🎮 Ваш профиль</h3>
                    <div class="user-stats">
                        <p><strong>Баланс:</strong> ${Utils.formatMoney(userData.balance)}</p>
                        <p><strong>Прибыль:</strong> ${Utils.formatMoney(userData.total_profit)}</p>
                        <p><strong>Покупки:</strong> ${userData.purchases}</p>
                        <p><strong>Любимый товар:</strong> ${userData.wants}</p>
                        <p><strong>Нелюбимый товар:</strong> ${userData.no_wants}</p>
                    </div>
                </div>
            `;
        }
    }
    
    /**
     * Возвращает текстовое описание статуса игры
     * @param {string} status - Статус игры
     * @returns {string} - Описание статуса
     */
    function getStatusText(status) {
        const statusMap = {
            'waiting': 'Ожидание начала',
            'playing': 'Игра идет',
            'finished': 'Игра завершена'
        };
        return statusMap[status] || 'Неизвестный статус';
    }
    
    /**
     * Обновляет состояние кнопок управления
     */
    function updateButtons() {
        const isPlaying = gameState.game.status === 'playing';
        const isFinished = gameState.game.status === 'finished';
        
        startGameBtn.disabled = isPlaying;
        nextRoundBtn.disabled = !isPlaying || isFinished;
        resetGameBtn.disabled = false;
    }
    
    /**
     * Обновляет отображение текущего лота
     */
    function updateCurrentLot() {
        if (gameState.game.current_lot) {
            const lot = gameState.game.current_lot;
            const canBuy = userData && userData.balance >= lot.price;
            
            currentLotEl.innerHTML = `
                <div class="lot-info">
                    <h3>${lot.name}</h3>
                    <div class="lot-details">
                        <p><strong>Количество:</strong> ${lot.quantity} шт.</p>
                        <p><strong>Цена:</strong> ${Utils.formatMoney(lot.price)}</p>
                        <p><strong>Себестоимость:</strong> ${Utils.formatMoney(lot.cost)}</p>
                        <p><strong>Потенциальная прибыль:</strong> ${Utils.formatMoney(lot.cost - lot.price)}</p>
                    </div>
                    ${userData ? `
                        <div class="user-actions">
                            <button id="buyButton" class="btn btn-primary" ${!canBuy ? 'disabled' : ''} 
                                    onclick="buyProduct(${lot.id})">
                                ${canBuy ? 'Купить за ' + Utils.formatMoney(lot.price) : 'Недостаточно средств'}
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        } else {
            currentLotEl.innerHTML = '<p>Выберите лот для торгов</p>';
        }
    }
    
    /**
     * Обновляет список игроков
     */
    function updatePlayersList() {
        if (gameState.players && gameState.players.length > 0) {
            playersListEl.innerHTML = gameState.players.map(player => `
                <div class="player-card">
                    <div class="player-avatar">${player.name.charAt(0)}</div>
                    <h3>${player.name}</h3>
                    <p>Баланс: ${Utils.formatMoney(player.balance)}</p>
                    <p>Прибыль: ${Utils.formatMoney(player.total_profit)}</p>
                    <p>Покупки: ${player.purchases}</p>
                </div>
            `).join('');
        } else {
            playersListEl.innerHTML = '<p>Загрузка игроков...</p>';
        }
    }
    
    /**
     * Обновляет отображение ставок и результата
     */
    function updateBidsAndResult() {
        // Обновляем ставки
        if (gameState.game.bids && Object.keys(gameState.game.bids).length > 0) {
            const bidsArray = Object.values(gameState.game.bids);
            bidsArray.sort((a, b) => b.amount - a.amount);
            
            bidsListEl.innerHTML = bidsArray.map((bid, index) => `
                <div class="bid-item ${index === 0 ? 'winner' : ''}">
                    <span>${bid.player_name}</span>
                    <span>${Utils.formatMoney(bid.amount)}</span>
                </div>
            `).join('');
        } else {
            bidsListEl.innerHTML = '<p>Ставки появятся здесь</p>';
        }
        
        // Обновляем результат
        if (gameState.game.result) {
            const result = gameState.game.result;
            auctionResultEl.innerHTML = `
                <div class="result-info">
                    <h3>🏆 ${result.winner_name}</h3>
                    <p><strong>Ставка:</strong> ${Utils.formatMoney(result.winning_bid)}</p>
                    <p><strong>Продажа:</strong> ${Utils.formatMoney(result.selling_price)}</p>
                    <p><strong>Прибыль:</strong> ${Utils.formatMoney(result.profit)}</p>
                    <p><strong>Осталось:</strong> ${result.remaining_quantity} шт.</p>
                </div>
            `;
        } else {
            auctionResultEl.innerHTML = '<p>Результат торгов появится здесь</p>';
        }
    }
    
    /**
     * Начинает новую игру
     */
    async function startGame() {
        try {
            Utils.showLoading(true);
            const response = await API.post('/api/game/start');
            
            if (response.success) {
                Utils.showNotification('Игра начата!', 'success');
                if (response.user_data) {
                    userData = response.user_data;
                }
                await loadGameState();
            } else {
                Utils.showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка запуска игры:', error);
            Utils.showNotification('Ошибка запуска игры', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }
    
    /**
     * Покупает товар пользователем
     */
    async function buyProduct(productId) {
        try {
            Utils.showLoading(true);
            const response = await API.post('/api/user/buy', { product_id: productId });
            
            if (response.success) {
                Utils.showNotification(response.message, 'success');
                userData = response.user_data;
                await loadGameState();
            } else {
                Utils.showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка покупки товара:', error);
            Utils.showNotification('Ошибка покупки товара', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }
    
    // Делаем функцию покупки глобальной
    window.buyProduct = buyProduct;
    
    /**
     * Переходит к следующему раунду
     */
    async function nextRound() {
        try {
            Utils.showLoading(true);
            const response = await API.post('/api/game/next-round');
            
            if (response.success) {
                // Обновляем состояние игры
                gameState.game.round = response.round;
                gameState.game.current_lot = response.current_lot;
                gameState.game.bids = response.bids;
                gameState.game.result = response.result;
                
                if (response.game_over) {
                    gameState.game.status = 'finished';
                    Utils.showNotification(response.message, 'info');
                }
                
                updateUI();
                
            } else {
                Utils.showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка проведения раунда:', error);
            Utils.showNotification('Ошибка проведения раунда', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }
    
    /**
     * Сбрасывает игру
     */
    async function resetGame() {
        try {
            Utils.showLoading(true);
            const response = await API.post('/api/game/reset');
            
            if (response.success) {
                Utils.showNotification('Игра сброшена!', 'success');
                await loadGameState();
            } else {
                Utils.showNotification(response.message, 'error');
            }
            
        } catch (error) {
            console.error('Ошибка сброса игры:', error);
            Utils.showNotification('Ошибка сброса игры', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }
    
    // Обработчики событий
    startGameBtn.addEventListener('click', startGame);
    nextRoundBtn.addEventListener('click', nextRound);
    resetGameBtn.addEventListener('click', resetGame);
    
    // Загружаем начальное состояние
    loadGameState();
    
    // Обновляем состояние каждые 5 секунд
    setInterval(loadGameState, 5000);
});
