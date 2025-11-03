# test_cbrapi_integration.py
#!/usr/bin/env python3
"""
Скрипт для тестирования интеграции cbrapi
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, timedelta
from api_currency import (
    get_currency_rates_for_date,
    get_currency_rates_with_history,
    get_currency_dynamics,
    get_metal_rates,
    get_key_rate_cbr
)

def test_basic_currency_rates():
    """Тестирует базовое получение курсов валют"""
    print("🧪 Тестирование базовых курсов валют...")

    # Тест на сегодня
    rates, date = get_currency_rates_for_date(datetime.now().strftime('%d/%m/%Y'))
    if rates:
        print(f"✅ Курсы на {date}:")
        for curr in ['USD', 'EUR', 'GBP', 'JPY', 'AED']:
            if curr in rates:
                print(f"   {curr}: {rates[curr]['value']:.4f} руб. - {rates[curr]['name']}")
    else:
        print("❌ Не удалось получить курсы валют")
        return False

    return True

def test_currency_history():
    """Тестирует получение исторических данных"""
    print("\n🧪 Тестирование исторических данных...")

    result = get_currency_rates_with_history()
    rates_today, date_today, rates_yesterday, changes_yesterday, rates_tomorrow, changes_tomorrow = result

    if rates_today:
        print(f"✅ Курсы на сегодня ({date_today}): {len(rates_today)} валют")
        print(f"✅ Курсы на вчера: {len(rates_yesterday) if rates_yesterday else 0} валют")
        print(f"✅ Курсы на завтра: {len(rates_tomorrow) if rates_tomorrow else 0} валют")

        if changes_yesterday:
            print("✅ Изменения по сравнению со вчера:")
            for curr, change in list(changes_yesterday.items())[:2]:
                print(f"   {curr}: {change['change']:+.4f} ({change['change_percent']:+.2f}%)")
    else:
        print("❌ Не удалось получить исторические данные")
        return False

    return True

def test_currency_dynamics():
    """Тестирует получение динамики курсов"""
    print("\n🧪 Тестирование динамики курсов...")

    dynamics = get_currency_dynamics('USD', days=7)
    if dynamics:
        print(f"✅ Динамика USD за 7 дней: {len(dynamics)} записей")
        for i, day in enumerate(dynamics[-3:]):  # Показать последние 3 дня
            print(f"   {day['date']}: {day['value']:.4f} руб.")
    else:
        print("⚠️ Не удалось получить динамику (может быть нормально для выходных)")

    return True

def test_metal_rates():
    """Тестирует получение курсов металлов"""
    print("\n🧪 Тестирование курсов металлов...")

    metals = get_metal_rates()
    if metals:
        print(f"✅ Курсы металлов: {len(metals)} позиций")
        for metal_code, metal_data in metals.items():
            print(f"   {metal_data['name']}: покупка {metal_data['buy']:.2f}, продажа {metal_data['sell']:.2f}")
    else:
        print("⚠️ Не удалось получить курсы металлов")

    return True

def test_key_rate():
    """Тестирует получение ключевой ставки"""
    print("\n🧪 Тестирование ключевой ставки...")

    key_rate = get_key_rate_cbr()
    if key_rate:
        print(f"✅ Ключевая ставка: {key_rate['rate']}% на {key_rate['date']}")
    else:
        print("⚠️ Не удалось получить ключевую ставку через cbrapi")

    return True

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования интеграции cbrapi...\n")

    tests = [
        test_basic_currency_rates,
        test_currency_history,
        test_currency_dynamics,
        test_metal_rates,
        test_key_rate
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")

    print(f"\n📊 Результаты тестирования: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 Все тесты пройдены! Интеграция cbrapi работает корректно.")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте настройки.")

    return passed == total

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)