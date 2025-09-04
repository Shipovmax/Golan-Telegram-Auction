const stateEl = document.getElementById('status-text');
const priceEl = document.getElementById('price');
const nameEl = document.getElementById('p-name');
const descEl = document.getElementById('p-desc');
const colorsEl = document.getElementById('colors');
const demandEl = document.getElementById('demand');
const progressBar = document.getElementById('progress-bar');
const buyBtn = document.getElementById('buy-btn');
const waitBtn = document.getElementById('wait-btn');
const balanceEl = document.getElementById('balance');
const dealsList = document.getElementById('deals-list');
const HUMAN_ID = 'human';

async function fetchState(){ const r = await fetch('/api/state'); return await r.json(); }
async function fetchBalances(){ const r = await fetch('/api/balances'); return await r.json(); }
async function fetchDeals(){ const r = await fetch('/api/deals?limit=5'); return await r.json(); }
async function sendAction(action){ const r = await fetch('/api/human/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ action, player_id: HUMAN_ID })}); return await r.json(); }
function fmtPrice(x){ return Math.round(x*100)/100; }

async function render(){
  try{
    const s = await fetchState();
    const b = await fetchBalances();
    const deals = await fetchDeals();
    nameEl.textContent = s.product.name;
    descEl.textContent = s.product.description;
    colorsEl.textContent = 'Цвета оптом: ' + s.product.wholesale_colors.join(', ');
    demandEl.textContent = 'Спрос (розница): ' + Math.round(s.product.retail_demand_index*100) + '%';
    priceEl.textContent = fmtPrice(s.current_price) + ' ₽';
    const span = s.product.starting_price - s.product.min_price;
    const pos = Math.max(0, Math.min(1, (s.current_price - s.product.min_price) / (span || 1)));
    progressBar.style.width = (pos*100) + '%';
    // balance display
    balanceEl.textContent = 'Баланс: ' + (b[HUMAN_ID] !== undefined ? fmtPrice(b[HUMAN_ID]) + ' ₽' : '—');
    // deals
    dealsList.innerHTML = '';
    for(const d of deals){ const li = document.createElement('li'); li.textContent = `${d.product_name} — ${d.winner_name || '—'} — ${d.price} ₽`; dealsList.appendChild(li); }

    if(!s.running){
      if(s.reason === 'sold'){
        if(s.winner_id === HUMAN_ID){ stateEl.textContent = 'Вы купили лот по цене ' + fmtPrice(s.current_price) + ' ₽ 🎉'; }
        else { stateEl.textContent = 'Лот продан: ' + (s.winner_name || 'Покупатель') + ' за ' + fmtPrice(s.current_price) + ' ₽'; }
      } else if(s.reason === 'min_reached'){ stateEl.textContent = 'Минимальная цена достигнута. Лот не продан.'; }
      else { stateEl.textContent = 'Аукцион остановлен.'; }
      buyBtn.disabled = true; waitBtn.disabled = true;
    } else {
      stateEl.textContent = 'Аукцион идёт… Ждите снижения или покупайте!';
      buyBtn.disabled = false; waitBtn.disabled = false;
    }
  }catch(e){ stateEl.textContent = 'Ошибка соединения с сервером'; }
}

buyBtn.addEventListener('click', async ()=>{ buyBtn.disabled=true; await sendAction('buy'); await render(); });
waitBtn.addEventListener('click', async ()=>{ waitBtn.disabled=true; await sendAction('wait'); setTimeout(()=>waitBtn.disabled=false,600); });

setInterval(render,1000); render();
