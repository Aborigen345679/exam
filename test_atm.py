import unittest  # Стандартный фреймворк для тестирования в Python
import sys
import os

# Добавляем путь к текущей директории в sys.path
# Это позволяет импортировать модули из одной папки
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем основной класс банкомата для тестирования
from atm_core import ATMCore


class TestATM(unittest.TestCase):
    """
    Основной класс тестов банкомата
    Наследуется от unittest.TestCase - каждый метод test_* будет запущен как отдельный тест
    """
    
    def setUp(self):
        """
        Метод подготовки перед КАЖДЫМ тестом
        Выполняется автоматически перед запуском каждого test_* метода
        Создает чистое окружение для каждого теста
        """
        # Создаем новый экземпляр банкомата для каждого теста
        # Это обеспечивает независимость тестов друг от друга
        self.atm = ATMCore()
        
        # Регистрируем новую тестовую карту
        # Используем self.assertTrue для проверки успеха операции
        success, msg, data = self.atm.register_new_card("1234", "Тест")
        self.assertTrue(success, f"Не удалось создать карту: {msg}")  # Если success == False, тест упадет
        
        # Сохраняем данные карты для использования в тестах
        self.card = data["number"]  # Номер карты (16 цифр)
        self.pin = "1234"           # PIN-код для входа
        
        # Авторизуемся и пополняем баланс для возможности проведения операций
        self.atm.login(self.card, self.pin)
        self.atm.deposit(50000)  # Кладем 50 000 ₽ на счет
    
    # ========== ТЕСТЫ АВТОРИЗАЦИИ И БЕЗОПАСНОСТИ ==========
    
    def test_01_login(self):
        """
        Тест 1: Успешный вход с правильным PIN-кодом
        Проверяет, что система корректно авторизует пользователя
        """
        # Пытаемся войти с правильными данными
        success, msg, data = self.atm.login(self.card, self.pin)
        
        # Ожидаем, что вход успешен (success == True)
        self.assertTrue(success)
        
        # Выводим подтверждение в консоль (только для информирования)
        print("✓ Тест 1 пройден: вход выполнен")
    
    def test_02_login_wrong_pin(self):
        """
        Тест 2: Отказ во входе с неверным PIN-кодом
        Проверяет, что система не пускает с неправильным паролем
        """
        # Пытаемся войти с неправильным PIN (0000 вместо 1234)
        success, msg, data = self.atm.login(self.card, "0000")
        
        # Ожидаем, что вход НЕ успешен (success == False)
        self.assertFalse(success)
        print("✓ Тест 2 пройден: неверный PIN отклонен")
    
    def test_03_check_balance(self):
        """
        Тест 3: Проверка баланса
        Убеждаемся, что метод возвращает корректное значение
        """
        balance = self.atm.check_balance()
        
        # Баланс не должен быть None (должен быть числом)
        self.assertIsNotNone(balance)
        
        # Баланс не может быть отрицательным
        self.assertGreaterEqual(balance, 0)
        
        print(f"✓ Тест 3 пройден: баланс = {balance}")
    
    # ========== ТЕСТЫ ФИНАНСОВЫХ ОПЕРАЦИЙ ==========
    
    def test_04_deposit(self):
        """
        Тест 4: Пополнение счета
        Проверяет, что баланс увеличивается на сумму пополнения
        """
        old = self.atm.check_balance()          # Запоминаем старый баланс
        success, msg, data = self.atm.deposit(1000)  # Пополняем на 1000 ₽
        
        # Проверяем успех операции
        self.assertTrue(success)
        
        # Проверяем, что новый баланс = старый + 1000
        self.assertEqual(data["new_balance"], old + 1000)
        print("✓ Тест 4 пройден: пополнение работает")
    
    def test_05_withdraw(self):
        """
        Тест 5: Снятие денег
        Проверяет, что баланс уменьшается на сумму снятия
        """
        old = self.atm.check_balance()
        success, msg, data = self.atm.withdraw(1000)
        
        self.assertTrue(success)
        # Баланс должен уменьшиться ровно на 1000 ₽
        self.assertEqual(data["new_balance"], old - 1000)
        print("✓ Тест 5 пройден: снятие работает")
    
    def test_06_withdraw_insufficient(self):
        """
        Тест 6: Попытка снять больше, чем есть на счете
        Проверяет защиту от снятия средств при недостаточном балансе
        """
        balance = self.atm.check_balance()
        
        # Пытаемся снять на 1000 ₽ больше, чем есть
        success, msg, data = self.atm.withdraw(balance + 1000)
        
        # Ожидаем, что операция НЕ будет выполнена
        self.assertFalse(success)
        print("✓ Тест 6 пройден: недостаток средств")
    
    def test_07_withdraw_not_multiple(self):
        """
        Тест 7: Снятие суммы, не кратной 50
        Банкомат выдает только купюрами по 50, 100, 200, 500, 1000, 2000, 5000 ₽
        Поэтому сумма должна быть кратна 50
        """
        # 123 не кратно 50 (остаток 23)
        success, msg, data = self.atm.withdraw(123)
        
        # Операция должна быть отклонена
        self.assertFalse(success)
        print("✓ Тест 7 пройден: проверка кратности 50")
    
    # ========== ТЕСТЫ ПЕРЕВОДОВ ==========
    
    def test_08_transfer(self):
        """
        Тест 8: Перевод средств на другую карту
        Проверяет, что деньги списываются с одной карты и зачисляются на другую
        """
        # Создаем вторую карту (карту получателя)
        success, msg, target_data = self.atm.register_new_card("5678", "Получатель")
        target = target_data["number"]  # Номер карты получателя
        
        old = self.atm.check_balance()  # Баланс отправителя до перевода
        
        # Переводим 1000 ₽ на карту получателя
        success, msg, data = self.atm.transfer(target, 1000)
        
        self.assertTrue(success)
        # Баланс отправителя должен уменьшиться на 1000 ₽
        self.assertEqual(data["new_balance"], old - 1000)
        print("✓ Тест 8 пройден: перевод работает")
    
    def test_09_transfer_to_self(self):
        """
        Тест 9: Попытка перевода на свою же карту
        Такая операция должна быть запрещена
        """
        # Пытаемся перевести с карты на ту же карту
        success, msg, data = self.atm.transfer(self.card, 1000)
        
        # Ожидаем отказ
        self.assertFalse(success)
        print("✓ Тест 9 пройден: перевод себе запрещен")
    
    # ========== ТЕСТЫ БЕЗОПАСНОСТИ ==========
    
    def test_10_pin_attempts(self):
        """
        Тест 10: Блокировка карты после 3 неудачных попыток ввода PIN
        Важная функция безопасности против подбора пароля
        """
        # 3 неверные попытки ввода PIN
        for i in range(3):
            self.atm.login(self.card, "0000")  # Каждая попытка неверная
        
        # 4-я попытка (даже с правильным PIN) должна быть заблокирована
        success, msg, data = self.atm.login(self.card, self.pin)
        
        # Ожидаем, что вход не выполнен
        self.assertFalse(success)
        # Сообщение должно содержать слово "блокирована"
        self.assertIn("блокирована", msg)
        print("✓ Тест 10 пройден: блокировка после 3 ошибок")
    
    # ========== ТЕСТЫ ПЛАТЕЖЕЙ И УСЛУГ ==========
    
    def test_11_mobile_payment(self):
        """
        Тест 11: Оплата мобильной связи
        Проверяет списание средств за услуги связи
        """
        old = self.atm.check_balance()
        
        # Оплачиваем мобильную связь: номер 9123456789, сумма 300 ₽, оператор MTS
        success, msg, data = self.atm.pay_mobile("9123456789", 300, "MTS")
        
        self.assertTrue(success)
        # Баланс должен уменьшиться на сумму платежа
        self.assertEqual(data["new_balance"], old - 300)
        print("✓ Тест 11 пройден: оплата связи")
    
    def test_12_credit_payment(self):
        """
        Тест 12: Погашение кредита
        Проверяет списание средств в счет погашения задолженности
        """
        old = self.atm.check_balance()
        
        # Погашаем кредитную карту на 5000 ₽
        success, msg, data = self.atm.pay_credit("credit_card", 5000)
        
        self.assertTrue(success)
        self.assertEqual(data["new_balance"], old - 5000)
        print("✓ Тест 12 пройден: оплата кредита")
    
    def test_13_utilities_payment(self):
        """
        Тест 13: Оплата коммунальных услуг (ЖКХ)
        Проверяет платежи за электричество, воду и т.д.
        """
        old = self.atm.check_balance()
        
        # Оплачиваем электричество: лицевой счет 123456, сумма 2000 ₽
        success, msg, data = self.atm.pay_utilities("electricity", "123456", 2000)
        
        self.assertTrue(success)
        self.assertEqual(data["new_balance"], old - 2000)
        print("✓ Тест 13 пройден: оплата ЖКХ")
    
    def test_14_movie_ticket(self):
        """
        Тест 14: Покупка билета в кино
        Проверяет сервис покупки билетов
        """
        old = self.atm.check_balance()
        
        # Покупаем билет на первый фильм (индекс 0) на сеанс в 10:30
        success, msg, data = self.atm.buy_movie_ticket(0, "10:30")
        
        self.assertTrue(success)
        # Баланс должен уменьшиться (цена билета разная для разных фильмов)
        self.assertLess(data["new_balance"], old)
        print("✓ Тест 14 пройден: покупка билета")
    
    # ========== ТЕСТЫ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ ==========
    
    def test_15_history(self):
        """
        Тест 15: Запись истории операций
        Проверяет, что каждая операция сохраняется в историю
        """
        # Выполняем две операции
        self.atm.deposit(100)   # Пополнение
        self.atm.withdraw(50)   # Снятие
        
        # Получаем историю (последние 10 операций)
        history = self.atm.get_history()
        
        # В истории должно быть как минимум 2 записи
        self.assertGreaterEqual(len(history), 2)
        print("✓ Тест 15 пройден: история работает")
    
    def test_16_receipt(self):
        """
        Тест 16: Генерация чека
        Проверяет создание чека с правильными полями
        """
        # Генерируем чек для тестовой операции
        receipt = self.atm.generate_receipt("Тест", 1000, "Детали")
        
        # Чек должен содержать уникальный ID
        self.assertIn("receipt_id", receipt)
        # Чек должен содержать дату и время
        self.assertIn("date", receipt)
        print("✓ Тест 16 пройден: чек создан")
    
    def test_17_card_number_generation(self):
        """
        Тест 17: Генерация номера карты
        Проверяет, что номера карт имеют правильный формат
        """
        card = self.atm.generate_card_number()
        
        # Номер должен содержать ровно 16 цифр
        self.assertEqual(len(card), 16)
        # Все символы должны быть цифрами
        self.assertTrue(card.isdigit())
        print("✓ Тест 17 пройден: генерация карты")
    
    def test_18_new_card_registration(self):
        """
        Тест 18: Регистрация новой карты
        Проверяет создание новой карты в системе
        """
        # Регистрируем новую карту с PIN 9999
        success, msg, data = self.atm.register_new_card("9999", "Новый")
        
        self.assertTrue(success)
        # В данных должен быть номер карты
        self.assertIn("number", data)
        print("✓ Тест 18 пройден: регистрация карты")
    
    def test_19_logout(self):
        """
        Тест 19: Выход из системы
        Проверяет, что после выхода доступ к функциям блокируется
        """
        success, msg = self.atm.logout()
        
        # Выход должен быть успешным
        self.assertTrue(success)
        
        # После выхода проверка баланса должна возвращать None
        # (пользователь не авторизован)
        balance = self.atm.check_balance()
        self.assertIsNone(balance)
        print("✓ Тест 19 пройден: выход из системы")
    
    def test_20_data_save(self):
        """
        Тест 20: Сохранение данных в файлы
        Проверяет персистентность данных (сохранение на диск)
        """
        # Выполняем операцию, которая должна сохраниться
        self.atm.deposit(777)
        
        # Проверяем, что хотя бы один файл с данными существует
        files_exist = os.path.exists("atm_cards.json") or os.path.exists("atm_users.json")
        
        self.assertTrue(files_exist)
        print("✓ Тест 20 пройден: данные сохранены")


def run_tests():
    """
    Функция запуска всех тестов с красивым выводом результатов
    """
    print("\n" + "="*60)
    print(" WWW-БАНК - ЗАПУСК ТЕСТОВ")
    print("="*60 + "\n")
    
    # Создаем набор тестов из класса TestATM
    # unittest автоматически найдет все методы, начинающиеся с test_
    suite = unittest.TestLoader().loadTestsFromTestCase(TestATM)
    
    # Запускаем тесты с verbosity=0 (минимальный вывод)
    # verbosity=0 - только общие результаты
    # verbosity=1 - точки (.) для каждого теста
    # verbosity=2 - подробный вывод
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Выводим статистику
    print("\n" + "="*60)
    print(" РЕЗУЛЬТАТЫ")
    print("="*60)
    
    # Подсчитываем пройденные тесты
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f" Пройдено: {passed}")
    print(f" Ошибок: {len(result.errors)}")    # Ошибки в самом коде тестов
    print(f" Падений: {len(result.failures)}") # Неудачные проверки (assert)
    
    # Итоговый вердикт
    if result.wasSuccessful():
        print("\n 🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! 🎉")
    else:
        print("\n ❌ ЕСТЬ ОШИБКИ! ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ❌")
    
    print("="*60 + "\n")


# ========== ТОЧКА ВХОДА ==========
# Блок выполняется только при прямом запуске файла
# (не выполняется при импорте как модуля)
if __name__ == "__main__":
    run_tests()
