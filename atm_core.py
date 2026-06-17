import json
import hashlib # Библиотека для работы с криптографическими хэш-функциями
import os # Позволяет работать с файловой системой
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
# Помогает статическим анализаторам кода и IDE 
# лучше понимать типы переменных, что повышает читаемость и надежность программы.


class ATMCore:
    """
    Расширенный класс банкомата, реализующий все основные функции:
    - Авторизация по PIN-коду с блокировкой при ошибках
    - Просмотр баланса, снятие/пополнение средств
    - Переводы между картами
    - Оплата услуг (мобильная связь, ЖКХ, кредиты)
    - Покупка билетов в кино
    - История операций и генерация чеков
    """
    
    def __init__(self, data_file: str = "atm_cards.json", users_file: str = "atm_users.json"):
        """
        Инициализация банкомата с указанием файлов для хранения данных
        
        Аргументы:
            data_file: файл с данными демо-карт (основные)
            users_file: файл с данными зарегистрированных пользователей
        """
        # Файлы для хранения данных
        self.data_file = data_file
        self.users_file = users_file
        
        # Текущая активная карта (после успешного входа)
         #Optional[str] эта переменная может быть либо строкой (str), либо None
        self.current_card: Optional[str] = None
        
        # Доступные номиналы купюр для выдачи (от крупных к мелким)
        self.banknotes = [5000, 2000, 1000, 500, 200, 100, 50]
        
        # Безопасность: максимальное количество попыток ввода PIN
        self.max_login_attempts = 3
        
        # Хранилище попыток входа: номер карты -> {count: int, blocked_until: datetime}
        self.login_attempts: Dict[str, Dict] = {}
        
        # ========== УСЛУГИ ==========
        
        # Операторы мобильной связи для оплаты
        self.mobile_operators = {
            "MTS": "МТС",
            "Beeline": "Билайн", 
            "MegaFon": "МегаФон",
            "Tele2": "Теле2"
        }
        
        # Список фильмов для покупки билетов
        # Каждый фильм содержит название, цену и доступные сеансы
        self.movies = [
            {"name": "Дюна: Часть 3", "price": 450, "time": "10:30, 13:45, 17:00, 20:15"},
            {"name": "Звёздные войны: Новый рассвет", "price": 400, "time": "11:00, 14:30, 18:00, 21:30"},
            {"name": "Мстители: Секретные войны", "price": 500, "time": "10:00, 13:15, 16:30, 19:45"},
            {"name": "Гарри Поттер: Возвращение", "price": 380, "time": "12:00, 15:30, 19:00"},
            {"name": "Аватар 3", "price": 550, "time": "11:30, 15:00, 18:30, 22:00"}
        ]
        
        # Типы кредитов и долгов для оплаты
        # Каждый тип имеет название и иконку для отображения в UI
        self.credit_types = {
            "credit_card": {"name": "Погашение кредитной карты", "icon": "💳"},
            "consumer_loan": {"name": "Потребительский кредит", "icon": "🏠"},
            "mortgage": {"name": "Ипотека", "icon": "🏡"},
            "car_loan": {"name": "Автокредит", "icon": "🚗"},
            "overdraft": {"name": "Овердрафт", "icon": "📊"},
            "tax_debt": {"name": "Налоговая задолженность", "icon": "📝"},
            "fines": {"name": "Штрафы ГИБДД", "icon": "🚔"},
            "utilities_debt": {"name": "Долги по ЖКХ", "icon": "⚡"}
        }
        
        # Создаём демонстрационные данные, если файлы не существуют
        self._init_demo_data()
    
    def _init_demo_data(self):
        """
        Создание демонстрационных карт и пользователей при первом запуске
        Демо-карты:
        - 4276 1234 5678 9012 / PIN: 1234 (баланс: 150 000 ₽)
        - 4276 9876 5432 1098 / PIN: 4321 (баланс: 75 000 ₽)
        """
        # Создаём файл с демо-картами, если он не существует
        if not os.path.exists(self.data_file):
            demo_cards = {
                "4276123456789012": {
                    "pin_hash": self._hash_pin("1234"),
                    "pin": "1234", 
                    "balance": 150000,
                    "holder_name": "Иванов Иван Иванович",
                    "card_type": "Дебетовая",
                    "bank": "АТМ-БАНК",
                    "valid_until": "05/2029",  # Срок действия: май 2029
                    "history": []  # Пустая история операций
                },
                "4276987654321098": {
                    "pin_hash": self._hash_pin("4321"),
                    "pin": "4321",
                    "balance": 75000,
                    "holder_name": "Петров Петр Петрович",
                    "card_type": "Дебетовая",
                    "bank": "АТМ-БАНК",
                    "valid_until": "08/2028",
                    "history": []
                }
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(demo_cards, f, ensure_ascii=False, indent=2)
        
        # Создаём пустой файл пользователей, если он не существует
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _hash_pin(self, pin: str) -> str:
        """
        Хэширование PIN-кода с использованием SHA-256
        
        Аргументы:
            pin: PIN-код (4 цифры)
        
        Возвращает:
            Хэш-строку (64 символа в hex-формате)
        """
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def _load_cards(self) -> Dict[str, Any]:
        """Загрузка данных всех карт из файла demo cards"""
        if not os.path.exists(self.data_file):
            self._init_demo_data()
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_cards(self, cards: Dict[str, Any]):
        """Сохранение данных карт в файл demo cards"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)
    
    def _load_users(self) -> Dict[str, Any]:
        """Загрузка данных зарегистрированных пользователей"""
        # проверка существования файла
        if not os.path.exists(self.users_file):
            return {}
        with open(self.users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_users(self, users: Dict[str, Any]):
        """Сохранение данных пользователей"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    
    def clean_card_number(self, number: str) -> str:
        """ Очистка номера карты от пробелов и других символов """
        return number.replace(' ', '')
    
    def generate_card_number(self) -> str:
        """Генерация нового номера карты"""
        prefix = "4276"  # Префикс банка 
        random_part = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        return prefix + random_part
    
    def generate_balance(self) -> int:
        """Генерация случайного начального баланса для новой карты """
        return random.randint(10000, 50000)
    
    def register_new_card(self, pin: str, holder_name: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """ Регистрация новой карты в системе"""
        # Проверка формата PIN
        if len(pin) != 4 or not pin.isdigit():
            return False, "PIN должен состоять из 4 цифр", None
        
        users = self._load_users()
        cards = self._load_cards()
        
        # Генерация уникального номера карты
        while True:
            card_number = self.generate_card_number()
            # Убеждаемся, что номер не занят ни в одном файле
            if card_number not in cards and card_number not in users:
                break
        
        balance = self.generate_balance()
        
        # Формируем данные новой карты
        card_data = {
            "pin_hash": self._hash_pin(pin),
            "pin": pin,  # Сохраняем для простой проверки
            "balance": balance,
            "holder_name": holder_name or "Новый пользователь",
            "card_type": "Дебетовая",
            "bank": "WWW-БАНК",
            "valid_until": "06/2031",  # Срок действия 5 лет
            "history": [],
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        
        # Сохраняем в файл пользователей
        users[card_number] = card_data
        self._save_users(users)
        
        return True, "Карта успешно создана", {
            "number": card_number,
            "balance": balance,
            "pin": pin
        }
    
    def login(self, card_number: str, pin: str) -> Tuple[bool, str, Optional[Dict]]:
        """Авторизация пользователя по номеру карты и PIN-коду
        С защитой от подбора: 3 попытки, затем блокировка на 5 минут """
        clean_number = self.clean_card_number(card_number)
        #очистка от пробелов
        # Проверка блокировки карты
        if clean_number in self.login_attempts:
            attempts = self.login_attempts[clean_number]
            if 'blocked_until' in attempts:
                if datetime.now() < attempts['blocked_until']:
                    remaining = (attempts['blocked_until'] - datetime.now()).seconds // 60 + 1
                    return False, f"Карта заблокирована на {remaining} мин.", None
                else:
                    # Блокировка истекла, удаляем запись
                    del self.login_attempts[clean_number]
        
        # Валидация формата номера карты
        if not clean_number.isdigit() or len(clean_number) != 16:
            return False, "Некорректный номер карты (16 цифр)", None
        
        # Загрузка всех карт из обоих файлов
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        # Проверка существования карты
        if clean_number not in all_cards:
            return False, "Карта не найдена в системе", None
        
        card_data = all_cards[clean_number]
        
        # Проверка PIN-кода
        if card_data.get("pin") != pin:
            # Увеличиваем счётчик неудачных попыток
            if clean_number not in self.login_attempts:
                self.login_attempts[clean_number] = {'count': 1}
            else:
                self.login_attempts[clean_number]['count'] += 1
            
            attempts_left = self.max_login_attempts - self.login_attempts[clean_number]['count']
            
            # Если попытки закончились - блокируем
            if attempts_left <= 0:
                self.login_attempts[clean_number]['blocked_until'] = datetime.now() + timedelta(minutes=5)
                return False, "Карта заблокирована на 5 минут", None
            
            return False, f"Неверный PIN-код. Осталось попыток: {attempts_left}", None
        
        # Успешный вход: очищаем историю попыток
        if clean_number in self.login_attempts:
            del self.login_attempts[clean_number]
        
        self.current_card = clean_number
        
        # Возвращаем данные для сессии 
        return True, "Вход выполнен успешно", {
            "number": clean_number,
            "holder_name": card_data.get("holder_name", ""),
            "balance": card_data["balance"],
            "masked": f"**** {clean_number[-4:]}",  # Маскированный номер для отображения
            "card_type": card_data.get("card_type", "Дебетовая"),
            "bank": card_data.get("bank", "АТМ-БАНК"),
            "valid_until": card_data.get("valid_until", "")
        }
    
    def check_balance(self) -> Optional[int]:
        """Проверка текущего баланса"""
        if not self.current_card:
            return None
        all_cards = {**self._load_cards(), **self._load_users()}
        return all_cards[self.current_card]["balance"]
    
    def withdraw(self, amount: int) -> Tuple[bool, str, Optional[Dict]]:
        """ Снятие наличных с выдачей оптимального набора купюр"""
        if not self.current_card:
            return False, "Нет авторизации", None
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        balance = all_cards[self.current_card]["balance"]
        
        # Валидация суммы
        if amount <= 0:
            return False, "Некорректная сумма", None
        if amount > balance:
            return False, "Недостаточно средств", None
        
        # Проверка кратности минимальной купюре
        min_banknote = min(self.banknotes)
        if amount % min_banknote != 0:
            return False, f"Сумма должна быть кратна {min_banknote} руб.", None
        
        # Алгоритм выдачи купюр 
        remaining = amount
        banknotes_to_give = {}
        
        for banknote in self.banknotes:
            count = remaining // banknote
            if count > 0:
                banknotes_to_give[banknote] = count
                remaining -= count * banknote
        
        # Если не удалось разложить сумму точно
        if remaining > 0:
            return False, "Невозможно выдать точную сумму", None
        
        # Списание средств
        all_cards[self.current_card]["balance"] -= amount
        self._add_history(all_cards, self.current_card, "снятие", amount)
        
        # Сохранение изменений в соответствующий файл
        if self.current_card in cards:
            cards[self.current_card] = all_cards[self.current_card]
            self._save_cards(cards)
        else:
            users[self.current_card] = all_cards[self.current_card]
            self._save_users(users)
        
        return True, "Операция выполнена", {
            "banknotes": banknotes_to_give,  # Словарь {номинал: количество}
            "amount": amount,
            "new_balance": all_cards[self.current_card]["balance"]
        }
    
    def deposit(self, amount: int) -> Tuple[bool, str, Optional[Dict]]:
        """Пополнение баланса карты"""
        if not self.current_card:
            return False, "Нет авторизации", None
        if amount <= 0:
            return False, "Некорректная сумма", None
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        # Увеличение баланса
        all_cards[self.current_card]["balance"] += amount
        self._add_history(all_cards, self.current_card, "пополнение", amount)
        
        # Сохранение
        if self.current_card in cards:
            cards[self.current_card] = all_cards[self.current_card]
            self._save_cards(cards)
        else:
            users[self.current_card] = all_cards[self.current_card]
            self._save_users(users)
        
        return True, "Баланс пополнен", {
            "amount": amount,
            "new_balance": all_cards[self.current_card]["balance"]
        }
    
    def transfer(self, target_card: str, amount: int) -> Tuple[bool, str, Optional[Dict]]:
        """Перевод средств на другую карту"""
        if not self.current_card:
            return False, "Нет авторизации", None
        
        clean_target = self.clean_card_number(target_card)
        
        # Запрет перевода самому себе
        if clean_target == self.current_card:
            return False, "Нельзя перевести на ту же карту", None
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        # Проверка существования карты получателя
        if clean_target not in all_cards:
            return False, "Карта получателя не найдена", None
        
        # Валидация суммы
        if amount <= 0:
            return False, "Некорректная сумма", None
        if amount > all_cards[self.current_card]["balance"]:
            return False, "Недостаточно средств", None
        
        # Списание со счета отправителя
        all_cards[self.current_card]["balance"] -= amount
        self._add_history(all_cards, self.current_card, "перевод", amount)
        
        # Зачисление получателю
        all_cards[clean_target]["balance"] += amount
        self._add_history(all_cards, clean_target, "зачисление", amount)
        
        # Сохранение изменений для обеих карт
        for cn in [self.current_card, clean_target]:
            if cn in cards:
                cards[cn] = all_cards[cn]
            else:
                users[cn] = all_cards[cn]
        
        self._save_cards(cards)
        self._save_users(users)
        
        return True, "Перевод выполнен", {
            "amount": amount,
            "new_balance": all_cards[self.current_card]["balance"],
            "target_masked": f"****{clean_target[-4:]}"  # Маскированный номер получателя
        }
    
    def pay_credit(self, credit_type: str, amount: int, account: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """Погашение кредита или долга"""
        if not self.current_card:
            return False, "Нет авторизации", None
        
        # Проверка типа кредита
        if credit_type not in self.credit_types:
            return False, "Неверный тип кредита", None
        
        if amount <= 0:
            return False, "Некорректная сумма", None
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        # Проверка  средств
        if amount > all_cards[self.current_card]["balance"]:
            return False, "Недостаточно средств", None
        
        # Списание средств
        all_cards[self.current_card]["balance"] -= amount
        credit_name = self.credit_types[credit_type]["name"]
        self._add_history(all_cards, self.current_card, f"погашение {credit_name}", amount)
        
        # Сохранение
        if self.current_card in cards:
            cards[self.current_card] = all_cards[self.current_card]
            self._save_cards(cards)
        else:
            users[self.current_card] = all_cards[self.current_card]
            self._save_users(users)
        
        return True, "Платеж выполнен", {
            "amount": amount,
            "credit_type": credit_name,
            "new_balance": all_cards[self.current_card]["balance"]
        }
    
    def pay_mobile(self, phone: str, amount: int, operator: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """Оплата мобильной связи"""
        if not self.current_card:
            return False, "Нет авторизации", None
        
        # Валидация номера телефона
        if not phone.isdigit() or len(phone) < 10:
            return False, "Некорректный номер телефона", None
        
        # Ограничение суммы для мобильной связи
        if amount <= 0 or amount > 10000:
            return False, "Сумма от 1 до 10000 руб.", None
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        if amount > all_cards[self.current_card]["balance"]:
            return False, "Недостаточно средств", None
        
        # Списание
        all_cards[self.current_card]["balance"] -= amount
        self._add_history(all_cards, self.current_card, f"моб.связь {operator}", amount)
        
        # Сохранение
        if self.current_card in cards:
            cards[self.current_card] = all_cards[self.current_card]
            self._save_cards(cards)
        else:
            users[self.current_card] = all_cards[self.current_card]
            self._save_users(users)
        
        return True, "Оплата выполнена", {
            "amount": amount,
            "phone": phone,
            "new_balance": all_cards[self.current_card]["balance"]
        }
    
    def pay_utilities(self, service: str, account: str, amount: int) -> Tuple[bool, str, Optional[Dict]]:
        """Оплата коммунальных услуг (ЖКХ) """
        if not self.current_card:
            return False, "Нет авторизации", None
        
        if amount <= 0:
            return False, "Некорректная сумма", None
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        if amount > all_cards[self.current_card]["balance"]:
            return False, "Недостаточно средств", None
        
        # Списание
        all_cards[self.current_card]["balance"] -= amount
        self._add_history(all_cards, self.current_card, f"ЖКХ {service}", amount)
        
        # Сохранение
        if self.current_card in cards:
            cards[self.current_card] = all_cards[self.current_card]
            self._save_cards(cards)
        else:
            users[self.current_card] = all_cards[self.current_card]
            self._save_users(users)
        
        return True, "Оплата ЖКХ выполнена", {
            "amount": amount,
            "service": service,
            "new_balance": all_cards[self.current_card]["balance"]
        }
    
    def buy_movie_ticket(self, movie_index: int, time: str) -> Tuple[bool, str, Optional[Dict]]:
        """ Покупка билета в кино"""
        if not self.current_card:
            return False, "Нет авторизации", None
        
        # Проверка индекса фильма
        if movie_index < 0 or movie_index >= len(self.movies):
            return False, "Неверный выбор фильма", None
        
        movie = self.movies[movie_index]
        amount = movie["price"]  # Цена билета фиксирована для фильма
        
        cards = self._load_cards()
        users = self._load_users()
        all_cards = {**cards, **users}
        
        if amount > all_cards[self.current_card]["balance"]:
            return False, "Недостаточно средств", None
        
        # Списание
        all_cards[self.current_card]["balance"] -= amount
        self._add_history(all_cards, self.current_card, f"кино {movie['name']}", amount)
        
        # Сохранение
        if self.current_card in cards:
            cards[self.current_card] = all_cards[self.current_card]
            self._save_cards(cards)
        else:
            users[self.current_card] = all_cards[self.current_card]
            self._save_users(users)
        
        return True, "Билет куплен", {
            "movie": movie["name"],
            "time": time,
            "price": amount,
            "new_balance": all_cards[self.current_card]["balance"]
        }
    
    def _add_history(self, cards: Dict, card_number: str, operation: str, amount: int):
        """Добавление записи в историю операций карты (внутренний метод)"""
        entry = {
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "operation": operation,
            "amount": amount,
            "balance_after": cards[card_number]["balance"]  # Баланс после операции
        }
        cards[card_number]["history"].append(entry)
        
        # Ограничиваем историю 50 последними записями (для экономии памяти)
        if len(cards[card_number]["history"]) > 50:
            cards[card_number]["history"] = cards[card_number]["history"][-50:]
    
    def get_history(self) -> List[Dict]:
        """Получение последних 10 операций по текущей карте"""
        if not self.current_card:
            return []
        all_cards = {**self._load_cards(), **self._load_users()}
        # Возвращаем последние 10 операций в обратном порядке
        return list(reversed(all_cards[self.current_card]["history"][-10:]))
    
    def generate_receipt(self, operation: str, amount: int, details: str = "") -> Dict:
        """Генерация чека об операции """
        return {
            "bank": "АТМ-БАНК",
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "card": f"****{self.current_card[-4:]}" if self.current_card else "****",
            "operation": operation,
            "amount": amount,
            "details": details,
            "receipt_id": f"RCP-{random.randint(100000, 999999)}",  # Уникальный ID чека
            "terminal": f"ATM-{random.randint(1000, 9999)}"  # ID терминала
        }
    
    def logout(self) -> Tuple[bool, str]:
        """Выход из системы (завершение сессии)"""
        self.current_card = None
        return True, "Вы вышли из системы"
    
    def format_currency(self, amount: int) -> str:
        """Форматирование суммы в читаемый вид с разделителями тысяч"""
        return f"{amount:,} ₽".replace(",", " ")

# Создание глобального экземпляра банкомата для использования в других модулях
atm = ATMCore()