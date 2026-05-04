from datetime import date
from decimal import Decimal

import requests
from django.core.management.base import BaseCommand

from expenses.models import CurrencyRate


class Command(BaseCommand):
    """
    Команда для автоматического обновления
    Текущего курса валют с помощью API Цетробанка.
    """
    help = "Команда для обновления курса валют"

    def handle(self, *args, **options):
        url = "https://www.cbr-xml-daily.ru/daily_json.js"

        try:
            response = requests.get(url, timeout=15)
            data = response.json()

            currencies = ["USD", "EUR", "CNY"]
            updated_currencies = []

            for code in currencies:
                if code in data["Valute"]:
                    rate = Decimal(str(data["Valute"][code]["Value"]))

                    CurrencyRate.objects.update_or_create(
                        currency=code,
                        defaults={
                            "rate": rate,
                            "date": date.today(),
                        },
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"Курс {code} - {rate} ₽ успешно обновлён")
                    )
                    updated_currencies.append(code)
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Курс {code} не найден в ответе ЦБ")
                    )

            if len(updated_currencies) > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nУспешно обновлены курсы: {updated_currencies}"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING("Ни один курс не был обновлён"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка: {e}"))
