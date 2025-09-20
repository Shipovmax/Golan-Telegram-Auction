// JavaScript для страницы статистики
document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы DOM
    const refreshStatsBtn = document.getElementById('refreshStats');
    const gameStatusEl = document.getElementById('gameStatus');
    const totalProfitEl = document.getElementById('totalProfit');
    const totalPurchasesEl = document.getElementById('totalPurchases');
    const bestPlayerEl = document.getElementById('bestPlayer');
    const playersRankingEl = document.getElementById('playersRanking');
    const productsStatsEl = document.getElementById('productsStats');
    
    // Состояние статистики
    let statsData = {
        players: [],
        total_profit: 0,
        total_purchases: 0,
        best_player: '',
        game_info: {}
    };
    
    /**
     * Загружает статистику с сервера
     */
    async function loadStatistics() {
        try {
            Utils.showLoading(true);
            const response = await API.get('/api/statistics');
            
            statsData = response;
            updateStatisticsUI();
            
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
            Utils.showNotification('Ошибка загрузки статистики', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }
    
    /**
     * Обновляет интерфейс статистики
     */
    function updateStatisticsUI() {
        // Обновляем общую статистику
        updateGeneralStats();
        
        // Обновляем рейтинг игроков
        updatePlayersRanking();
        
        // Обновляем статистику товаров
        updateProductsStats();
    }
    
    /**
     * Обновляет общую статистику
     */
    function updateGeneralStats() {
        // Статус игры
        gameStatusEl.textContent = getGameStatusText(statsData.game_info.status);
        
        // Общая прибыль
        totalProfitEl.textContent = Utils.formatMoney(statsData.total_profit);
        
        // Всего покупок
        totalPurchasesEl.textContent = Utils.formatNumber(statsData.total_purchases);
        
        // Лучший игрок
        bestPlayerEl.textContent = statsData.best_player || 'Нет данных';
    }
    
    /**
     * Возвращает текстовое описание статуса игры
     * @param {string} status - Статус игры
     * @returns {string} - Описание статуса
     */
    function getGameStatusText(status) {
        const statusMap = {
            'waiting': 'Ожидание начала',
            'playing': 'Игра идет',
            'finished': 'Игра завершена'
        };
        return statusMap[status] || 'Неизвестный статус';
    }
    
    /**
     * Обновляет рейтинг игроков
     */
    function updatePlayersRanking() {
        if (statsData.players && statsData.players.length > 0) {
            // Создаем заголовок таблицы
            const header = `
                <div class="ranking-header">
                    <div>Место</div>
                    <div>Имя</div>
                    <div>Баланс</div>
                    <div>Прибыль</div>
                    <div>Покупки</div>
                    <div>Продажи</div>
                </div>
            `;
            
            // Создаем строки с игроками
            const playersRows = statsData.players.map((player, index) => {
                const profitClass = player.total_profit >= 0 ? 'positive' : 'negative';
                const profitText = player.total_profit >= 0 ? 
                    `+${Utils.formatMoney(player.total_profit)}` : 
                    Utils.formatMoney(player.total_profit);
                
                return `
                    <div class="ranking-item">
                        <div>${index + 1}</div>
                        <div>${player.name}</div>
                        <div>${Utils.formatMoney(player.balance)}</div>
                        <div class="${profitClass}">${profitText}</div>
                        <div>${player.purchases}</div>
                        <div>${player.sales}</div>
                    </div>
                `;
            }).join('');
            
            playersRankingEl.innerHTML = header + playersRows;
            
        } else {
            playersRankingEl.innerHTML = '<div class="loading">Нет данных об игроках</div>';
        }
    }
    
    /**
     * Обновляет статистику товаров
     */
    function updateProductsStats() {
        if (statsData.products && statsData.products.length > 0) {
            const productsCards = statsData.products.map(product => `
                <div class="product-stat-card">
                    <h3>${product.name}</h3>
                    <p><strong>Цена:</strong> ${Utils.formatMoney(product.price)}</p>
                    <p><strong>Количество:</strong> ${product.quantity} шт.</p>
                    <p><strong>Себестоимость:</strong> ${Utils.formatMoney(product.cost)}</p>
                </div>
            `).join('');
            
            productsStatsEl.innerHTML = productsCards;
            
        } else {
            productsStatsEl.innerHTML = '<div class="loading">Нет данных о товарах</div>';
        }
    }
    
    /**
     * Обновляет статистику
     */
    async function refreshStatistics() {
        await loadStatistics();
        Utils.showNotification('Статистика обновлена!', 'success');
    }
    
    // Обработчик события для кнопки обновления
    refreshStatsBtn.addEventListener('click', refreshStatistics);
    
    // Загружаем начальную статистику
    loadStatistics();
    
    // Обновляем статистику каждые 10 секунд
    setInterval(loadStatistics, 10000);
});
