"""
================================================================================
                    ВЕБ-СЕРВЕР БАНКОМАТА "WWW-БАНК"
================================================================================
"""

import os          # Работа с файловой системой
import sys         # Системные функции
import json        # Преобразование данных в JSON
import socket      # Поиск свободного порта
import random      # Генерация случайных чисел
import threading   # Отложенное открытие браузера
import webbrowser  # Открытие браузера
from http.server import HTTPServer, BaseHTTPRequestHandler  # HTTP-сервер
from atm_core import atm  # Основная логика банкомата


def get_free_port():
    """Находит свободный порт в системе."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def get_html():
    """Генерирует HTML-страницу с встроенными данными."""
    
    all_cards = {**atm._load_cards(), **atm._load_users()}
    
    for card_num in all_cards:
        if 'history' in all_cards[card_num]:
            all_cards[card_num]['history'] = list(reversed(all_cards[card_num]['history'][-10:]))
    
    cards_data = json.dumps(all_cards, ensure_ascii=False)
    movies_data = json.dumps(atm.movies, ensure_ascii=False)
    operators_data = json.dumps(atm.mobile_operators, ensure_ascii=False)
    banknotes_data = json.dumps(atm.banknotes)
    credit_types_data = json.dumps(atm.credit_types, ensure_ascii=False)
    
    return '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">  <!-- Кодировка UTF-8 для русского языка -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">  <!-- Адаптация под мобильные -->
<title>WWW-БАНК</title>  <!-- Заголовок вкладки браузера -->
<style>
:root {  /* CSS переменные цветовой схемы */
    --bg: #0d0d0d;  /* Основной фон страницы */
    --card-bg: #1a1a1a;  /* Фон карточек */
    --gold: #ffd700;  /* Золотой цвет акцентов */
    --white: #ffffff;  /* Белый текст */
    --gray: #aaaaaa;  /* Серый текст */
    --border: #333333;  /* Цвет границ */
    --error: #ff4444;  /* Красный для ошибок */
    --success: #44ff44;  /* Зелёный для успеха */
    --input-bg: #222222;  /* Фон полей ввода */
}
* { margin:0; padding:0; box-sizing:border-box; }  /* Сброс отступов у всех элементов */
body {  /* Стили для всей страницы */
    font-family: 'Segoe UI', Arial, sans-serif;  /* Шрифт */
    background: var(--bg);  /* Тёмный фон */
    color: var(--white);  /* Белый текст */
    min-height: 100vh;  /* Минимум на всю высоту экрана */
    display: flex;  /* Flexbox для центрирования */
    align-items: center;  /* Центр по вертикали */
    justify-content: center;  /* Центр по горизонтали */
    padding: 20px;  /* Отступы по краям */
}
.container {  /* Основной контейнер (корпус банкомата) */
    width: 100%;  /* На всю ширину родителя */
    max-width: 960px;  /* Максимальная ширина */
    background: var(--card-bg);  /* Тёмный фон */
    border: 2px solid var(--border);  /* Рамка */
    border-radius: 24px;  /* Скругление углов */
    overflow: hidden;  /* Скрываем выходящее за границы */
    box-shadow: 0 20px 60px rgba(255,215,0,0.08);  /* Тень */
}
.header {  /* Шапка */
    background: #111;  /* Почти чёрный фон */
    border-bottom: 3px solid var(--gold);  /* Золотая полоса снизу */
    padding: 22px 32px;  /* Внутренние отступы */
    display: flex;  /* Flexbox для выравнивания */
    align-items: center;  /* Центр по вертикали */
    justify-content: space-between;  /* Логотип слева, часы справа */
}
.logo { display:flex; align-items:center; gap:14px; }  /* Блок логотипа */
.logo-box {  /* Квадрат с иконкой глобуса */
    width: 52px; height: 52px;  /* Размер */
    background: linear-gradient(135deg, #ffd700, #ffaa00);  /* Золотой градиент */
    border-radius: 14px;  /* Скругление */
    display: flex; align-items: center; justify-content: center;  /* Центровка содержимого */
    font-size: 28px; color: #000; font-weight: 900;  /* Иконка внутри */
    box-shadow: 0 4px 20px rgba(255,215,0,0.35);  /* Свечение */
}
.logo-name {  /* Название банка */
    font-size: 26px; font-weight: 900;  /* Размер и жирность */
    color: var(--gold); letter-spacing: 1px;  /* Золотой цвет, расстояние между буквами */
}
.header-info {  /* Правая часть шапки */
    display: flex; align-items: center; gap: 16px;  /* Flexbox */
    font-size: 13px; color: var(--gray);  /* Серый текст */
}
.live-dot {  /* Анимированная точка "в сети" */
    width: 10px; height: 10px; border-radius: 50%;  /* Круг */
    background: var(--gold);  /* Золотой цвет */
    animation: glow 2s infinite;  /* Бесконечная анимация пульсации */
}
@keyframes glow {  /* Анимация свечения точки */
    0%,100%{box-shadow:0 0 6px var(--gold);}  /* Слабое свечение */
    50%{box-shadow:0 0 20px var(--gold);}  /* Сильное свечение */
}
.content {  /* Основное содержимое (меняется через JS) */
    padding: 28px 32px;  /* Отступы */
    min-height: 500px;  /* Минимальная высота */
    display: flex; align-items: center; justify-content: center;  /* Центровка */
}
.footer {  /* Подвал */
    background: #111;  /* Тёмный фон */
    border-top: 1px solid var(--border);  /* Рамка сверху */
    padding: 12px 32px;  /* Отступы */
    display: flex; align-items: center; justify-content: space-between;  /* Flexbox */
    font-size: 12px; color: var(--gray);  /* Серый мелкий текст */
}
.page { width: 100%; animation: slide 0.35s ease; }  /* Анимация появления страниц */
@keyframes slide { from{opacity:0;transform:translateY(18px);} to{opacity:1;transform:translateY(0);} }  /* Плавный выезд снизу */
.btn {  /* Общие стили для всех кнопок */
    padding: 16px 28px; border-radius: 16px; font-size: 16px;  /* Отступы, скругление, размер */
    font-weight: 700; cursor: pointer; border: none;  /* Жирный шрифт, курсор-рука, без рамки */
    transition: all 0.2s; font-family: inherit;  /* Плавные переходы, шрифт как у родителя */
    display: inline-flex; align-items: center; gap: 10px;  /* Flex для выравнивания */
    justify-content: center; letter-spacing: 0.3px; min-width: 120px;  /* Центровка, межбуквенное расстояние */
}
.btn:active { transform: scale(0.96); }  /* Эффект нажатия (сжатие) */
.btn-gold {  /* Золотая кнопка (главное действие) */
    background: linear-gradient(135deg, #ffd700, #ffaa00);  /* Золотой градиент */
    color: #000; box-shadow: 0 6px 20px rgba(255,215,0,0.25);  /* Чёрный текст, тень */
}
.btn-gold:hover { box-shadow: 0 10px 30px rgba(255,215,0,0.45); transform: translateY(-3px); }  /* При наведении: сильнее тень, приподнимается */
.btn-outline {  /* Кнопка с обводкой */
    background: transparent; color: var(--white);  /* Прозрачный фон, белый текст */
    border: 2px solid var(--gold);  /* Золотая рамка */
}
.btn-outline:hover { background: rgba(255,215,0,0.08); transform: translateY(-3px); }  /* При наведении: полупрозрачный фон */
.btn-white { background: var(--white); color: #000; }  /* Белая кнопка, чёрный текст */
.btn-white:hover { background: #e0e0e0; transform: translateY(-3px); }  /* При наведении: светлее */
.btn-close { background: transparent; color: var(--error); border: 2px solid var(--error); }  /* Красная кнопка выхода */
.btn-close:hover { background: rgba(255,68,68,0.08); }  /* При наведении: полупрозрачный красный */
.btn-sm { padding: 10px 20px; font-size: 14px; border-radius: 12px; min-width: auto; }  /* Маленькая кнопка */
.btn-block { width: 100%; }  /* Кнопка на всю ширину */
.form-group { margin-bottom: 14px; }  /* Группа полей формы */
.form-group label {  /* Подписи к полям */
    display: block; font-size: 12px; font-weight: 700;  /* Блочный элемент, мелкий жирный */
    color: var(--gray); text-transform: uppercase;  /* Серый, ЗАГЛАВНЫЕ БУКВЫ */
    letter-spacing: 1px; margin-bottom: 8px;  /* Расстояние между буквами, отступ снизу */
}
.form-input {  /* Поле ввода */
    width: 100%; padding: 15px 18px; background: var(--input-bg);  /* На всю ширину, отступы, тёмный фон */
    border: 2px solid var(--border); border-radius: 14px;  /* Рамка, скругление */
    color: var(--white); font-size: 16px; font-family: inherit;  /* Белый текст, шрифт как у родителя */
    transition: all 0.3s;  /* Плавные переходы */
}
.form-input:focus {  /* Поле в фокусе */
    outline: none; border-color: var(--gold);  /* Убираем стандартную обводку, золотая рамка */
    box-shadow: 0 0 0 4px rgba(255,215,0,0.1);  /* Золотое свечение */
}
.form-input::placeholder { color: #555; }  /* Цвет плейсхолдера */
.form-select {  /* Выпадающий список */
    width: 100%; padding: 15px 18px; background: var(--input-bg);  /* На всю ширину, отступы, тёмный фон */
    border: 2px solid var(--border); border-radius: 14px;  /* Рамка, скругление */
    color: var(--white); font-size: 16px; font-family: inherit;  /* Белый текст */
    cursor: pointer;  /* Курсор-рука */
}
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }  /* Сетка из 2 колонок */
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }  /* Сетка из 3 колонок */
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }  /* Сетка из 4 колонок */
.op-card {  /* Карточка операции */
    background: var(--input-bg); border: 2px solid var(--border);  /* Тёмный фон, рамка */
    border-radius: 20px; padding: 24px 16px; text-align: center;  /* Скругление, отступы, центр */
    cursor: pointer; transition: all 0.3s;  /* Курсор-рука, плавные переходы */
}
.op-card:hover { border-color: var(--gold); background: #2a2a2a; transform: translateY(-4px); box-shadow: 0 12px 30px rgba(255,215,0,0.12); }  /* При наведении: золотая рамка, приподнимается */
.op-emoji { font-size: 44px; margin-bottom: 10px; }  /* Иконка операции */
.op-title { font-size: 16px; font-weight: 700; color: var(--white); }  /* Название операции */
.quick-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 14px 0; }  /* Сетка быстрых кнопок */
.quick-btn {  /* Быстрая кнопка суммы */
    padding: 14px 10px; background: var(--input-bg);  /* Отступы, тёмный фон */
    border: 2px solid var(--border); border-radius: 14px;  /* Рамка, скругление */
    cursor: pointer; text-align: center; font-size: 15px;  /* Курсор-рука, центр, размер */
    font-weight: 700; color: var(--gold); transition: all 0.2s;  /* Жирный, золотой цвет, плавно */
    font-family: inherit;  /* Шрифт как у родителя */
}
.quick-btn:hover { border-color: var(--gold); background: rgba(255,215,0,0.1); transform: scale(1.04); box-shadow: 0 6px 18px rgba(255,215,0,0.15); }  /* При наведении: золотая рамка, увеличение */
.quick-btn:active { transform: scale(0.95); }  /* Эффект нажатия */
.card { background: var(--input-bg); border: 1px solid var(--border); border-radius: 18px; padding: 22px; margin-bottom: 16px; }  /* Универсальная карточка */
.big-balance { font-size: 68px; font-weight: 900; text-align: center; color: var(--gold); line-height: 1; padding: 10px; }  /* Крупный баланс */
.receipt {  /* Стиль чека */
    background: #fff; color: #000; border-radius: 16px;  /* Белый фон, чёрный текст, скругление */
    padding: 24px; font-family: 'Courier New', monospace;  /* Отступы, моноширинный шрифт */
    font-size: 13px; max-width: 380px; margin: 18px auto;  /* Размер, ширина, центровка */
    box-shadow: 0 8px 30px rgba(0,0,0,0.5); text-align: left;  /* Тень, текст слева */
}
.receipt-header { text-align: center; border-bottom: 2px dashed #ccc; padding-bottom: 10px; margin-bottom: 10px; }  /* Шапка чека */
.receipt-row { display: flex; justify-content: space-between; margin: 5px 0; }  /* Строка чека */
.receipt-total { border-top: 2px dashed #ccc; margin-top: 10px; padding-top: 10px; font-weight: 900; font-size: 15px; }  /* Итог чека */
.cash-slot { background: #111; border: 2px dashed var(--gold); border-radius: 18px; padding: 28px; text-align: center; margin: 16px 0; }  /* Слот выдачи наличных */
.history-list { max-height: 380px; overflow-y: auto; }  /* Список истории с прокруткой */
.history-row { border-bottom: 1px solid var(--border); padding: 14px 0; display: flex; justify-content: space-between; align-items: center; }  /* Строка истории */
.history-row:last-child { border: none; }  /* Убираем рамку у последней строки */
.h-date { font-size: 11px; color: var(--gray); }  /* Дата операции */
.h-op { font-size: 15px; font-weight: 600; margin-top: 3px; }  /* Название операции */
.h-amt { font-size: 18px; font-weight: 700; }  /* Сумма операции */
.amt-plus { color: var(--success); }  /* Зелёный для пополнений */
.amt-minus { color: var(--error); }  /* Красный для списаний */
.sec-title { font-size: 26px; font-weight: 900; text-align: center; color: var(--gold); margin-bottom: 4px; }  /* Заголовок секции */
.sec-subtitle { font-size: 14px; color: var(--gray); text-align: center; margin-bottom: 20px; }  /* Подзаголовок */
.error-msg { color: var(--error); font-size: 14px; min-height: 22px; text-align: center; margin: 8px 0; }  /* Сообщение об ошибке */
.success-msg { color: var(--success); font-size: 18px; font-weight: 700; text-align: center; margin: 10px 0; }  /* Сообщение об успехе */
.nfc-area { background: var(--input-bg); border: 3px dashed var(--gold); border-radius: 24px; padding: 40px; text-align: center; animation: nfcPulse 2s infinite; }  /* NFC-зона с пульсацией */
@keyframes nfcPulse {  /* Анимация пульсации NFC */
    0%,100% { border-color: var(--gold); box-shadow: 0 0 20px rgba(255,215,0,0.1); }  /* Золотая рамка */
    50% { border-color: #fff; box-shadow: 0 0 40px rgba(255,215,0,0.25); }  /* Белая рамка, сильное свечение */
}
.nfc-icon { font-size: 80px; animation: float 3s ease-in-out infinite; }  /* Иконка NFC с анимацией */
@keyframes float { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-14px);} }  /* Плавающая иконка */
::-webkit-scrollbar { width: 5px; }  /* Ширина скроллбара */
::-webkit-scrollbar-track { background: transparent; }  /* Прозрачный фон скроллбара */
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }  /* Цвет ползунка скроллбара */
@media (max-width: 700px) {  /* Адаптация для мобильных */
    .grid-3 { grid-template-columns: 1fr 1fr; }  /* 3 колонки -> 2 */
    .grid-4 { grid-template-columns: 1fr 1fr; }  /* 4 колонки -> 2 */
    .header { flex-direction: column; gap: 10px; padding: 16px; }  /* Шапка в столбик */
}
</style>
</head>
<body>
<div class="container">  <!-- Основной контейнер -->
    <div class="header">  <!-- Шапка -->
        <div class="logo">  <!-- Блок логотипа -->
            <div class="logo-box">🌐</div>  <!-- Иконка глобуса -->
            <div class="logo-name">WWW-БАНК</div>  <!-- Название банка -->
        </div>
        <div class="header-info">  <!-- Правая часть шапки -->
            <span id="clock"></span>  <!-- Сюда JS вставит часы -->
            <div class="live-dot"></div>  <!-- Анимированная точка "в сети" -->
        </div>
    </div>
    <div class="content" id="content"></div>  <!-- Основное содержимое (рендерится через JS) -->
    <div class="footer">  <!-- Подвал -->
        <span>🟡 Система онлайн</span>  <!-- Статус системы -->
        <span id="footerMsg">Вставьте карту</span>  <!-- Динамический статус -->
    </div>
</div>

<script>
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
const SAVE_ENDPOINT = '/api/save';  // URL для сохранения данных
const CARDS_ENDPOINT = '/api/cards';  // URL для получения карт

let ALL_CARDS = ''' + cards_data + ''';  // Все карты (встроены с сервера)
const MOVIES = ''' + movies_data + ''';  // Список фильмов
const OPERATORS = ''' + operators_data + ''';  // Операторы связи
const BANKNOTES = ''' + banknotes_data + ''';  // Номиналы купюр
const CREDIT_TYPES = ''' + credit_types_data + ''';  // Типы кредитов

let currentCard = null;  // Текущая активная карта (null = не авторизован)

// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
function $(id) { return document.getElementById(id); }  // Сокращение для getElementById
function fmt(n) { return n.toLocaleString('ru-RU') + ' ₽'; }  // Форматирование суммы
function render(h) { $('content').innerHTML = '<div class="page">' + h + '</div>'; }  // Рендер страницы
function setFooter(t) { $('footerMsg').textContent = t; }  // Установка текста в подвале

function tick() {  // Обновление часов
    const n = new Date();  // Текущая дата/время
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };  // Формат даты
    const dateStr = n.toLocaleDateString('ru-RU', options);  // Дата
    $('clock').textContent = dateStr + ' | ' + n.toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit', second:'2-digit'});  // Дата + время
}
tick(); setInterval(tick, 1000);  // Запуск часов, обновление каждую секунду

function formatCard(el) {  // Форматирование номера карты (пробелы каждые 4 цифры)
    let v = el.value.replace(/\\D/g, '').slice(0, 16);  // Удаляем всё кроме цифр, ограничиваем 16
    el.value = v.match(/.{1,4}/g)?.join(' ') || v;  // Группируем по 4 цифры с пробелами
}

async function saveData() {  // Сохранение данных на сервер
    try {
        await fetch(SAVE_ENDPOINT, {  // POST-запрос
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(ALL_CARDS)  // Отправляем все карты
        });
    } catch(e) { console.error('Ошибка сохранения:', e); }
}

function addHistory(op, amt) {  // Добавление записи в историю
    if (!ALL_CARDS[currentCard]) return;  // Если карты нет - выходим
    if (!ALL_CARDS[currentCard].history) ALL_CARDS[currentCard].history = [];  // Если истории нет - создаём
    ALL_CARDS[currentCard].history.unshift({  // Добавляем в начало массива
        date: new Date().toLocaleString('ru-RU'),  // Дата/время
        operation: op,  // Название операции
        amount: amt,  // Сумма
        balance_after: ALL_CARDS[currentCard].balance  // Баланс после операции
    });
    saveData();  // Сохраняем
}

function genReceipt(op, amt, details) {  // Генерация чека
    const rid = 'RCP-' + Math.floor(Math.random()*900000+100000);  // Уникальный ID чека
    const now = new Date().toLocaleString('ru-RU');  // Текущая дата/время
    const masked = currentCard ? '****' + currentCard.slice(-4) : '****';  // Маскируем карту
    let det = details ? '<div class="receipt-row"><span>Детали:</span><span>' + details + '</span></div>' : '';  // Детали если есть
    return '<div class="receipt"><div class="receipt-header"><strong>WWW-БАНК</strong><br>Чек #' + rid + '<br>' + now + '</div><div class="receipt-row"><span>Карта:</span><span>' + masked + '</span></div><div class="receipt-row"><span>Операция:</span><span>' + op + '</span></div>' + det + '<div class="receipt-row"><span>Сумма:</span><span>' + fmt(amt) + '</span></div><div class="receipt-total"><div class="receipt-row"><span>ИТОГО:</span><span>' + fmt(amt) + '</span></div></div></div>';  // HTML чека
}

// СТРАНИЦЫ ИНТЕРФЕЙСА
function pageLogin() {  // Страница входа
    currentCard = null;  // Сбрасываем сессию
    setFooter('👋 Вставьте карту');  // Статус в подвале
    render(` 
        <div style="max-width:460px;margin:0 auto;text-align:center;">
            <div style="font-size:70px;margin-bottom:10px;">🌐</div>
            <div class="sec-title">Добро пожаловать</div>
            <div class="sec-subtitle">Войдите по карте или добавьте новую</div>
            <div class="card">
                <div class="form-group">
                    <label>💳 Номер карты</label>
                    <input type="text" class="form-input" id="cardNum" placeholder="4276 1234 5678 9012" maxlength="19" oninput="formatCard(this)" autofocus>
                </div>
                <div class="form-group">
                    <label>🔐 PIN-код</label>
                    <input type="password" class="form-input" id="pinCode" placeholder="••••" maxlength="4" oninput="this.value=this.value.replace(/\\D/g,'').slice(0,4)">
                </div>
                <div class="error-msg" id="errLogin"></div>
                <button class="btn btn-gold btn-block" onclick="doLogin()">🔓 Войти</button>
            </div>
            <button class="btn btn-white btn-block" style="margin:12px 0;" onclick="pageNewCard()">🆕 Добавить карту</button>
        </div>
    `);
}

async function pageNewCard() {  // Страница добавления карты
    try {  // Загружаем свежие данные с сервера
        const resp = await fetch(CARDS_ENDPOINT);
        const data = await resp.json();
        ALL_CARDS = data;
    } catch(e) {}
    render(`  
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">🆕 Добавить карту</div>
            <div class="sec-subtitle">Приложите карту к NFC-метке</div>
            <div class="nfc-area" id="nfcArea" style="cursor:pointer;" onclick="activateNFC()">
                <div class="nfc-icon">📳</div>
                <div style="font-size:20px;font-weight:700;color:var(--gold);">NFC</div>
                <div style="font-size:13px;color:var(--gray);">Нажмите для активации</div>
            </div>
            <div class="card" id="pinSection" style="display:none;">
                <div class="sec-subtitle" style="font-size:14px;">Введите PIN-код</div>
                <div class="form-group">
                    <label>🔐 PIN-код (4 цифры)</label>
                    <input type="password" class="form-input" id="newPin" placeholder="••••" maxlength="4" oninput="this.value=this.value.replace(/\\D/g,'').slice(0,4)" autofocus>
                </div>
                <div class="error-msg" id="errNewCard"></div>
                <button class="btn btn-gold btn-block" onclick="createCard()">🎉 Добавить карту</button>
            </div>
            <button class="btn btn-outline btn-block" style="margin-top:12px;" onclick="pageLogin()">← Назад</button>
        </div>
    `);
}

function activateNFC() {  // Симуляция NFC-считывания
    const area = $('nfcArea');  // Находим NFC-зону
    area.innerHTML = '<div class="nfc-icon">✅</div><div style="font-size:20px;font-weight:700;color:#44ff44;">Карта считана!</div><div style="font-size:13px;color:var(--gray);">Теперь введите PIN</div>';  // Меняем содержимое
    area.style.animation = 'none';  // Отключаем анимацию
    area.style.borderColor = '#44ff44';  // Меняем цвет рамки на зелёный
    $('pinSection').style.display = 'block';  // Показываем поле для PIN
    setTimeout(() => $('newPin').focus(), 300);  // Фокус на поле PIN
}

async function createCard() {  // Создание новой карты
    const pin = $('newPin').value;  // PIN из поля
    const err = $('errNewCard');  // Элемент для ошибок
    if (pin.length !== 4) { err.textContent = '❌ PIN должен быть 4 цифры'; return; }  // Проверка PIN
    
    let cardNum;  // Номер карты
    do { cardNum = '4276' + Array.from({length:12}, () => Math.floor(Math.random()*10)).join(''); }  // Генерируем номер (4276 + 12 цифр)
    while (ALL_CARDS[cardNum]);  // Повторяем пока номер не станет уникальным
    
    const balance = Math.floor(Math.random() * 40000) + 10000;  // Случайный баланс от 10000 до 50000
    
    ALL_CARDS[cardNum] = {  // Создаём запись карты
        pin: pin,  // PIN
        balance: balance,  // Баланс
        holder_name: 'Новый пользователь',  // Владелец
        card_type: 'Дебетовая',  // Тип карты
        bank: 'WWW-БАНК',  // Банк
        valid_until: '05/2031',  // Срок действия
        history: [{date: new Date().toLocaleString('ru-RU'), operation: 'открытие', amount: balance, balance_after: balance}]  // История
    };
    
    await saveData();  // Сохраняем на сервер
    
    const formatted = cardNum.match(/.{1,4}/g).join(' ');  // Форматируем номер с пробелами
    alert('✅ Карта добавлена!\\n\\n💳 ' + formatted + '\\n🔐 PIN: ' + pin + '\\n💰 Баланс: ' + fmt(balance) + '\\n\\nЗАПОМНИТЕ ДАННЫЕ!');  // Показываем данные
    currentCard = cardNum;  // Устанавливаем текущую карту
    setFooter('💳 Карта: ****' + cardNum.slice(-4));  // Статус в подвале
    pageMenu();  // Переход в меню
}

function doLogin() {  // Обработка входа
    const cardNum = $('cardNum').value.trim().replace(/\\s/g, '');  // Номер карты (удаляем пробелы)
    const pin = $('pinCode').value.trim();  // PIN
    const err = $('errLogin');  // Элемент для ошибок
    
    if (cardNum.length !== 16) { err.textContent = '❌ Номер карты: 16 цифр'; return; }  // Проверка длины номера
    if (pin.length !== 4) { err.textContent = '❌ PIN: 4 цифры'; return; }  // Проверка длины PIN
    
    const cd = ALL_CARDS[cardNum];  // Находим карту
    if (!cd) { err.textContent = '❌ Карта не найдена'; return; }  // Карта не существует
    if (cd.pin !== pin) { err.textContent = '❌ Неверный PIN-код'; return; }  // Неверный PIN
    
    currentCard = cardNum;  // Устанавливаем текущую карту
    setFooter('💳 Карта: ****' + cardNum.slice(-4));  // Статус в подвале
    pageMenu();  // Переход в меню
}

function pageMenu() {  // Главное меню
    if (!currentCard) { pageLogin(); return; }  // Если не авторизован - на вход
    const cd = ALL_CARDS[currentCard];  // Данные текущей карты
    const masked = currentCard.slice(0,4) + ' ' + currentCard.slice(4,8) + ' ' + currentCard.slice(8,12) + ' ' + currentCard.slice(12);  // Номер с пробелами
    
    render(` 
        <div>
            <div class="card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div>
                    <div style="font-size:12px;color:var(--gray);">💳 Активная карта</div>
                    <div style="font-size:20px;font-weight:700;color:var(--gold);">${masked}</div>
                    <div style="font-size:13px;color:var(--gray);margin-top:4px;">💰 ${fmt(cd.balance)} | ${cd.card_type || 'Дебетовая'}</div>
                </div>
                <button class="btn btn-close btn-sm" onclick="doLogout()">🚪 Выйти</button>
            </div>
            <div style="text-align:center;font-size:14px;color:var(--gray);margin-bottom:16px;">Выберите операцию</div>
            <div class="grid-3">
                <div class="op-card" onclick="pageBalance()"><div class="op-emoji">💰</div><div class="op-title">Баланс</div></div>
                <div class="op-card" onclick="pageWithdraw()"><div class="op-emoji">💸</div><div class="op-title">Снять</div></div>
                <div class="op-card" onclick="pageDeposit()"><div class="op-emoji">📥</div><div class="op-title">Пополнить</div></div>
                <div class="op-card" onclick="pageTransfer()"><div class="op-emoji">💫</div><div class="op-title">Перевод</div></div>
                <div class="op-card" onclick="pageCredits()"><div class="op-emoji">🏛️</div><div class="op-title">Кредиты</div></div>
                <div class="op-card" onclick="pageMobile()"><div class="op-emoji">📱</div><div class="op-title">Связь</div></div>
                <div class="op-card" onclick="pageUtilities()"><div class="op-emoji">🏠</div><div class="op-title">ЖКХ</div></div>
                <div class="op-card" onclick="pageCinema()"><div class="op-emoji">🎬</div><div class="op-title">Кино</div></div>
            </div>
            <div style="text-align:center;margin-top:16px;">
                <button class="btn btn-outline btn-sm" onclick="pageHistory()">📋 История</button>
                <button class="btn btn-outline btn-sm" onclick="pageInfo()">ℹ️ Инфо</button>
            </div>
        </div>
    `);
}

function pageBalance() {  // Страница баланса
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    render(`<div style="text-align:center;"><div class="sec-subtitle">💰 Ваш баланс</div><div class="big-balance">${fmt(ALL_CARDS[currentCard].balance)}</div>${genReceipt('Запрос баланса', 0, '')}<button class="btn btn-gold" style="margin-top:24px;" onclick="pageMenu()">← Назад</button></div>`);
}

function pageWithdraw() {  // Страница снятия
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    const bal = ALL_CARDS[currentCard].balance;  // Баланс
    let qb = '';  // Быстрые кнопки
    [500,1000,2000,5000,10000,20000].forEach(a => { qb += '<button class="quick-btn" onclick="setWAmt('+a+')">💵 '+fmt(a)+'</button>'; });  // Создаём кнопки
    render(` 
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">💸 Снятие наличных</div>
            <div class="sec-subtitle">Доступно: ${fmt(bal)}</div>
            <div class="form-group"><label>Сумма (кратно 50 ₽)</label><input type="number" class="form-input" id="wAmt" placeholder="0" min="50" step="50" autofocus></div>
            <div class="error-msg" id="wErr"></div>
            <div class="quick-grid">${qb}</div>
            <div style="display:flex;gap:12px;margin-top:16px;">
                <button class="btn btn-gold" style="flex:1;" onclick="doWithdraw()">💸 Снять</button>
                <button class="btn btn-outline" style="flex:1;" onclick="pageMenu()">← Назад</button>
            </div>
            <div id="wResult"></div>
        </div>
    `);
}

function setWAmt(v) { $('wAmt').value=v; $('wAmt').focus(); }  // Установка суммы в поле

async function doWithdraw() {  // Обработка снятия
    const amt = parseInt($('wAmt').value);  // Сумма
    const err = $('wErr');  // Элемент для ошибок
    if (!amt||amt<=0||amt%50!==0) { err.textContent='❌ Сумма кратна 50 ₽'; return; }  // Проверка кратности 50
    if (amt>ALL_CARDS[currentCard].balance) { err.textContent='❌ Недостаточно средств'; return; }  // Проверка баланса
    
    let rem=amt; const bn={};  // Расчёт купюр
    for(const b of BANKNOTES) { const c=Math.floor(rem/b); if(c>0){bn[b]=c; rem-=c*b;} }  // Жадный алгоритм
    
    ALL_CARDS[currentCard].balance-=amt;  // Списание
    addHistory('снятие', -amt);  // Добавление в историю
    await saveData();  // Сохранение
    
    let bns=''; for(const[k,v] of Object.entries(bn)) bns+=v+'×'+k+'₽ ';  // Формируем строку с купюрами
    $('wResult').innerHTML=`${genReceipt('Снятие наличных', amt, 'Купюры: ' + bns)}<div class="cash-slot"><div style="font-size:44px;">💶</div><div style="font-size:20px;font-weight:700;color:var(--gold);">${fmt(amt)}</div><div style="font-size:12px;color:var(--gray);">${bns}</div></div><button class="btn btn-gold btn-block" onclick="pageMenu()">✅ Забрать</button>`;  // Показываем результат
}

function pageDeposit() {  // Страница пополнения
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    const bal = ALL_CARDS[currentCard].balance;  // Баланс
    let qb = '';  // Быстрые кнопки
    [500,1000,2000,5000,10000].forEach(a => qb+='<button class="quick-btn" onclick="setDAmt('+a+')">💰 '+fmt(a)+'</button>');  // Создаём кнопки
    render(`  
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">📥 Пополнение</div>
            <div class="sec-subtitle">Баланс: ${fmt(bal)}</div>
            <div class="cash-slot"><div style="font-size:40px;">🏧</div><div style="font-weight:600;color:var(--gold);">КУПЮРОПРИЕМНИК</div></div>
            <div class="form-group"><label>Сумма</label><input type="number" class="form-input" id="dAmt" placeholder="0" min="50" step="50" autofocus></div>
            <div class="error-msg" id="dErr"></div>
            <div class="quick-grid">${qb}</div>
            <div style="display:flex;gap:12px;margin-top:16px;">
                <button class="btn btn-white" style="flex:1;" onclick="doDeposit()">💰 Внести</button>
                <button class="btn btn-outline" style="flex:1;" onclick="pageMenu()">← Назад</button>
            </div>
            <div id="dResult"></div>
        </div>
    `);
}

function setDAmt(v) { $('dAmt').value=v; $('dAmt').focus(); }  // Установка суммы в поле

async function doDeposit() {  // Обработка пополнения
    const amt = parseInt($('dAmt').value);  // Сумма
    if(!amt||amt<=0) { $('dErr').textContent='❌ Введите сумму'; return; }  // Проверка суммы
    ALL_CARDS[currentCard].balance+=amt;  // Увеличение баланса
    addHistory('пополнение', amt);  // Добавление в историю
    await saveData();  // Сохранение
    $('dResult').innerHTML='<div class="success-msg">✅ Пополнено '+fmt(amt)+'!</div>' + genReceipt('Пополнение счета', amt, '');  // Показываем результат
}

function pageTransfer() {  // Страница перевода
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    render(` 
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">💫 Перевод</div>
            <div class="sec-subtitle">Доступно: ${fmt(ALL_CARDS[currentCard].balance)}</div>
            <div class="form-group"><label>💳 Карта получателя</label><input type="text" class="form-input" id="tCard" placeholder="4276 XXXX XXXX XXXX" maxlength="19" oninput="formatCard(this)" autofocus></div>
            <div class="form-group"><label>💰 Сумма</label><input type="number" class="form-input" id="tAmt" placeholder="0" min="1"></div>
            <div class="error-msg" id="tErr"></div>
            <div style="display:flex;gap:12px;margin-top:16px;">
                <button class="btn btn-gold" style="flex:1;" onclick="doTransfer()">💫 Перевести</button>
                <button class="btn btn-outline" style="flex:1;" onclick="pageMenu()">← Назад</button>
            </div>
            <div id="tResult"></div>
        </div>
    `);
}

async function doTransfer() {  // Обработка перевода
    const target=$('tCard').value.trim().replace(/\\s/g,'');  // Карта получателя
    const amt=parseInt($('tAmt').value);  // Сумма
    const err=$('tErr');  // Элемент для ошибок
    if(target.length!==16){err.textContent='❌ Номер карты: 16 цифр';return;}  // Проверка номера
    if(target===currentCard){err.textContent='❌ Нельзя себе';return;}  // Запрет перевода себе
    if(!amt||amt<=0||amt>ALL_CARDS[currentCard].balance){err.textContent='❌ Некорректная сумма';return;}  // Проверка суммы
    ALL_CARDS[currentCard].balance-=amt;  // Списание
    addHistory('перевод',-amt);  // Добавление в историю
    if(ALL_CARDS[target]) ALL_CARDS[target].balance+=amt;  // Зачисление получателю
    await saveData();  // Сохранение
    $('tResult').innerHTML='<div class="success-msg">✅ Переведено '+fmt(amt)+'!</div>' + genReceipt('Перевод на карту', amt, '****' + target.slice(-4));  // Показываем результат
}

function pageCredits() {  // Страница кредитов
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    let opts='';  // Опции для select
    for(const[k,v] of Object.entries(CREDIT_TYPES)) opts+='<option value="'+k+'">'+v.icon+' '+v.name+'</option>';  // Заполняем select
    render(` 
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">🏛️ Погашение кредитов и долгов</div>
            <div class="sec-subtitle">Доступно: ${fmt(ALL_CARDS[currentCard].balance)}</div>
            <div class="form-group"><label>Тип задолженности</label><select class="form-select" id="crType">${opts}</select></div>
            <div class="form-group"><label>💰 Сумма платежа</label><input type="number" class="form-input" id="crAmt" placeholder="0" min="1" autofocus></div>
            <div class="error-msg" id="crErr"></div>
            <div class="quick-grid">
                <button class="quick-btn" onclick="$('crAmt').value='1000'">1000 ₽</button>
                <button class="quick-btn" onclick="$('crAmt').value='3000'">3000 ₽</button>
                <button class="quick-btn" onclick="$('crAmt').value='5000'">5000 ₽</button>
                <button class="quick-btn" onclick="$('crAmt').value='10000'">10000 ₽</button>
                <button class="quick-btn" onclick="$('crAmt').value='20000'">20000 ₽</button>
                <button class="quick-btn" onclick="$('crAmt').value='50000'">50000 ₽</button>
            </div>
            <div style="display:flex;gap:12px;margin-top:16px;">
                <button class="btn btn-gold" style="flex:1;" onclick="doCredit()">🏛️ Оплатить</button>
                <button class="btn btn-outline" style="flex:1;" onclick="pageMenu()">← Назад</button>
            </div>
            <div id="crResult"></div>
        </div>
    `);
}

async function doCredit() {  // Обработка оплаты кредита
    const amt=parseInt($('crAmt').value);  // Сумма
    const err=$('crErr');  // Элемент для ошибок
    if(!amt||amt<=0||amt>ALL_CARDS[currentCard].balance){err.textContent='❌ Некорректная сумма';return;}  // Проверка суммы
    ALL_CARDS[currentCard].balance-=amt;  // Списание
    const ct=CREDIT_TYPES[$('crType').value];  // Тип кредита
    addHistory('погашение '+ct.name,-amt);  // Добавление в историю
    await saveData();  // Сохранение
    $('crResult').innerHTML='<div class="success-msg">✅ Платеж '+fmt(amt)+' выполнен!</div>' + genReceipt('Погашение: ' + ct.name, amt, '');  // Показываем результат
}

function pageMobile() {  // Страница мобильной связи
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    let ops=''; for(const[k,v] of Object.entries(OPERATORS)) ops+='<option value="'+k+'">'+v+'</option>';  // Опции операторов
    let qb=''; [100,200,300,500,1000].forEach(a => qb+='<button class="quick-btn" onclick="setMAmt('+a+')">📱 '+a+' ₽</button>');  // Быстрые кнопки
    render(`  
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">📱 Мобильная связь</div>
            <div class="sec-subtitle">Доступно: ${fmt(ALL_CARDS[currentCard].balance)}</div>
            <div class="form-group"><label>📡 Оператор</label><select class="form-select" id="mOp">${ops}</select></div>
            <div class="form-group"><label>📞 Телефон</label><input type="tel" class="form-input" id="mPhone" placeholder="9XX XXX XX XX" autofocus></div>
            <div class="form-group"><label>💰 Сумма</label><input type="number" class="form-input" id="mAmt" placeholder="0" min="1"></div>
            <div class="error-msg" id="mErr"></div>
            <div class="quick-grid">${qb}</div>
            <div style="display:flex;gap:12px;margin-top:16px;">
                <button class="btn btn-white" style="flex:1;" onclick="doMobile()">📱 Оплатить</button>
                <button class="btn btn-outline" style="flex:1;" onclick="pageMenu()">← Назад</button>
            </div>
            <div id="mResult"></div>
        </div>
    `);
}

function setMAmt(v){$('mAmt').value=v;$('mAmt').focus();}  // Установка суммы

async function doMobile(){  // Обработка оплаты мобильной связи
    const amt=parseInt($('mAmt').value);  // Сумма
    const phone=$('mPhone').value.trim();  // Телефон
    if(!amt||amt<=0||amt>ALL_CARDS[currentCard].balance){$('mErr').textContent='❌ Некорректная сумма';return;}  // Проверка суммы
    if(!phone||phone.length<10){$('mErr').textContent='❌ Введите телефон';return;}  // Проверка телефона
    ALL_CARDS[currentCard].balance-=amt;  // Списание
    const opName = OPERATORS[$('mOp').value] || '';  // Оператор
    addHistory('моб.связь '+opName,-amt);  // Добавление в историю
    await saveData();  // Сохранение
    $('mResult').innerHTML='<div class="success-msg">✅ Оплачено!</div>' + genReceipt('Мобильная связь: ' + opName, amt, 'Тел: ' + phone);  // Показываем результат
}

function pageUtilities() {  // Страница ЖКХ
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    render(` 
        <div style="max-width:500px;margin:0 auto;text-align:center;">
            <div class="sec-title">🏠 ЖКХ</div>
            <div class="sec-subtitle">Доступно: ${fmt(ALL_CARDS[currentCard].balance)}</div>
            <div class="form-group"><label>📋 Услуга</label><select class="form-select" id="uSvc"><option value="electricity">⚡ Электроэнергия</option><option value="water">💧 Вода</option><option value="gas">🔥 Газ</option><option value="heating">🌡️ Отопление</option></select></div>
            <div class="form-group"><label>🔢 Лицевой счет</label><input type="text" class="form-input" id="uAcc" placeholder="1234567890" autofocus></div>
            <div class="form-group"><label>💰 Сумма</label><input type="number" class="form-input" id="uAmt" placeholder="0" min="1"></div>
            <div class="error-msg" id="uErr"></div>
            <div class="quick-grid">
                <button class="quick-btn" onclick="$('uAmt').value='500'">500 ₽</button>
                <button class="quick-btn" onclick="$('uAmt').value='1000'">1000 ₽</button>
                <button class="quick-btn" onclick="$('uAmt').value='2000'">2000 ₽</button>
            </div>
            <div style="display:flex;gap:12px;margin-top:16px;">
                <button class="btn btn-white" style="flex:1;" onclick="doUtil()">🏠 Оплатить</button>
                <button class="btn btn-outline" style="flex:1;" onclick="pageMenu()">← Назад</button>
            </div>
            <div id="uResult"></div>
        </div>
    `);
}

async function doUtil(){  // Обработка оплаты ЖКХ
    const amt=parseInt($('uAmt').value);  // Сумма
    const acc=$('uAcc').value.trim();  // Лицевой счет
    if(!amt||amt<=0||amt>ALL_CARDS[currentCard].balance){$('uErr').textContent='❌ Некорректная сумма';return;}  // Проверка суммы
    if(!acc){$('uErr').textContent='❌ Введите лицевой счет';return;}  // Проверка счета
    ALL_CARDS[currentCard].balance-=amt;  // Списание
    const svc = $('uSvc').selectedOptions[0].text;  // Услуга
    addHistory('ЖКХ ' + svc,-amt);  // Добавление в историю
    await saveData();  // Сохранение
    $('uResult').innerHTML='<div class="success-msg">✅ Оплачено!</div>' + genReceipt('ЖКХ: ' + svc, amt, 'Счет: ' + acc);  // Показываем результат
}

function pageCinema() {  // Страница кино
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    let mc=''; MOVIES.forEach((m,i) => { mc+='<div class="op-card" onclick="selMov('+i+')"><div class="op-emoji">🎬</div><div class="op-title">'+m.name+'</div><div style="font-size:12px;color:var(--gray);">'+m.price+' ₽</div></div>'; });  // Карточки фильмов
    render(` 
        <div style="text-align:center;">
            <div class="sec-title">🎬 Кино</div>
            <div class="sec-subtitle">Доступно: ${fmt(ALL_CARDS[currentCard].balance)}</div>
            <div class="grid-2" style="margin-bottom:16px;">${mc}</div>
            <div class="card" id="bkForm" style="display:none;">
                <div class="form-group"><label>🎬 Фильм</label><input type="text" class="form-input" id="mvName" readonly></div>
                <div class="form-group"><label>🕐 Время</label><select class="form-select" id="mvTime"></select></div>
                <div class="form-group"><label>🎫 Билетов</label><input type="number" class="form-input" id="mvTickets" value="1" min="1" max="5"></div>
                <button class="btn btn-gold btn-block" onclick="buyMov()">🎫 Купить</button>
            </div>
            <button class="btn btn-outline btn-block" style="margin-top:8px;" onclick="pageMenu()">← Назад</button>
            <div id="mvResult"></div>
        </div>
    `);
    window.selMovIdx=-1;  // Сброс выбранного фильма
}

function selMov(i){  // Выбор фильма
    window.selMovIdx=i; const m=MOVIES[i];  // Сохраняем индекс фильма
    $('mvName').value=m.name;  // Название фильма
    const s=$('mvTime'); s.innerHTML='';  // Очищаем список времени
    m.time.split(', ').forEach(t=>{const o=document.createElement('option');o.textContent=t;s.appendChild(o);});  // Добавляем времена сеансов
    $('bkForm').style.display='block'; $('bkForm').scrollIntoView({behavior:'smooth'});  // Показываем форму
}

async function buyMov(){  // Покупка билетов
    if(window.selMovIdx<0) return;  // Если фильм не выбран - выходим
    const m=MOVIES[window.selMovIdx]; const t=parseInt($('mvTickets').value); const total=m.price*t;  // Стоимость билетов
    if(total>ALL_CARDS[currentCard].balance){alert('❌ Недостаточно средств!');return;}  // Проверка баланса
    ALL_CARDS[currentCard].balance-=total;  // Списание
    addHistory('кино: '+m.name,-total);  // Добавление в историю
    await saveData();  // Сохранение
    $('mvResult').innerHTML='<div class="success-msg">✅ Билетов: '+t+' на "'+m.name+'"</div>' + genReceipt('Кино: ' + m.name, total, t + ' билет(а), ' + $('mvTime').value);  // Показываем результат
}

function pageInfo() {  // Информационная страница
    const now = new Date();  // Текущая дата
    const dateStr = now.toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });  // Форматируем дату
    render(` 
        <div style="max-width:600px;margin:0 auto;text-align:center;">
            <div class="sec-title">ℹ️ Информация</div>
            <div class="card" style="text-align:left;line-height:2;">
                <strong>🌐 WWW-БАНК</strong><br>
                📅 ${dateStr}<br>
                💳 Услуги: баланс, снятие, пополнение, переводы, кредиты, связь, ЖКХ, кино<br>
                🔐 Безопасность: PIN-коды, блокировка после 3 попыток<br>
                📞 Поддержка: 8-800-555-35-35
            </div>
            <button class="btn btn-gold btn-block" onclick="pageMenu()">← Назад</button>
        </div>
    `);
}

function pageHistory() {  // Страница истории
    if (!currentCard) return pageLogin();  // Если не авторизован - на вход
    const hist = ALL_CARDS[currentCard].history || [];  // История операций
    let items='';  // Строка для HTML
    if(hist.length===0) items='<div style="text-align:center;color:var(--gray);padding:40px;">📭 История пуста</div>';  // Если история пуста
    else hist.slice(0,10).forEach(op=>{  // Берём последние 10 операций
        const minus=['снятие','перевод','моб.связь','ЖКХ','кино','погашение'].some(kw => op.operation.toLowerCase().includes(kw.toLowerCase()));  // Определяем тип операции
        items+='<div class="history-row"><div><div class="h-date">'+op.date+'</div><div class="h-op">'+op.operation+'</div></div><div class="h-amt '+(minus?'amt-minus':'amt-plus')+'">'+(minus?'-':'+')+Math.abs(op.amount).toLocaleString('ru-RU')+' ₽</div></div>';  // Строка истории
    });
    render('<div style="max-width:650px;margin:0 auto;"><div class="sec-title">📋 История</div><div class="history-list">'+items+'</div><button class="btn btn-gold btn-block" style="margin-top:16px;" onclick="pageMenu()">← Назад</button></div>');  
}

function doLogout() {  // Выход из системы
    currentCard = null;  // Сбрасываем сессию
    setFooter('👋 Вы вышли из системы');  // Статус в подвале
    pageLogin();  // На страницу входа
}

pageLogin();  // Запуск приложения со страницы входа
</script>
</body>
</html>'''


class ATMHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для встроенного веб-сервера."""
    
    def get_html_content(self):
        return get_html()
    
    def do_GET(self):
        if self.path == '/api/cards':
            cards = atm._load_cards()
            users = atm._load_users()
            all_cards = {**cards, **users}
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(all_cards, ensure_ascii=False).encode('utf-8'))
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(self.get_html_content().encode('utf-8'))
    
    def do_POST(self):
        if self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                cards = atm._load_cards()
                users = atm._load_users()
                
                for card_num, card_data in data.items():
                    if card_num in cards:
                        cards[card_num] = card_data
                    else:
                        users[card_num] = card_data
                
                atm._save_cards(cards)
                atm._save_users(users)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
        
        self.send_response(404)
        self.end_headers()
    
    def log_message(self, format, *args):
        pass


def main():
    port = get_free_port()
    server = HTTPServer(('127.0.0.1', port), ATMHandler)
    url = f'http://127.0.0.1:{port}'
    
    print(f'  🌐  {url}')
    
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 Завершено. Все данные сохранены.')
        server.shutdown()


if __name__ == '__main__':
    main()