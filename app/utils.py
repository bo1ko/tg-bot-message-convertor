import re


def replace_prices_with_uah(text, exchange_rate):
    pattern = r"\$(\d{1,3}(?:,\d{3})*)(?:[.,]\d{2})?"

    def convert_to_uah(match):
        dollars = float(match.group().replace("$", "").replace(",", "."))
        price_in_uah = round(dollars * exchange_rate)

        return f"{price_in_uah} грн + вага\n"

    return re.sub(pattern, convert_to_uah, text)

def bold_words(words, sentence):
    # Створюємо регулярний вираз для кожного слова, яке потрібно знайти
    for word in words:
        sentence = re.sub(rf'\b({re.escape(word)})\b', r'<b>\1</b>', sentence)
    return sentence
