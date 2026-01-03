"""
Утилиты для определения типа устройства
"""


def is_mobile_device(user_agent):
    """
    Определяет, является ли устройство мобильным телефоном.
    
    Логика:
    - mobile: iPhone / Android phone
    - pc: всё остальное (включая планшеты)
    
    Args:
        user_agent: HTTP User-Agent строка
        
    Returns:
        bool: True если устройство мобильный телефон, False иначе
    """
    if not user_agent:
        return False
    
    ua_lower = user_agent.lower()
    
    # iPhone / iPod
    if 'iphone' in ua_lower or 'ipod' in ua_lower:
        return True
    
    # Android phone (но не планшет)
    if 'android' in ua_lower:
        # Планшеты обычно имеют 'tablet' или 'pad' в UA
        if 'tablet' in ua_lower or 'pad' in ua_lower:
            return False
        # Проверяем на мобильные браузеры Android
        if 'mobile' in ua_lower:
            return True
    
    return False

def ua_genitive_phrase(text: str) -> str:
    """
    Очень аккуратная эвристика под кейсы приглашений:
    - "Ярослав" -> "Ярослава"
    - "Сергій" -> "Сергія"
    - "Світлана" -> "Світлани"
    - "мама Світлана" -> "мами Світлани"
    - "тато Сергій" -> "тата Сергія"
    Не претендует на 100% лингвистику, но решает твои примеры.
    """
    if not text:
        return text

    s = " ".join(text.strip().split())
    words = s.split(" ")
    if not words:
        return s

    # словарь “родственник/роль” -> род.падеж
    role_map = {
        "мама": "мами",
        "тато": "тата",
        "бабуся": "бабусі",
        "дідусь": "дідуся",
        "хрещена": "хрещеної",
        "хрещений": "хрещеного",
    }

    def inflect_word(w: str) -> str:
        lw = w.lower()

        # роли
        if lw in role_map:
            # сохраняем оригинальный регистр первой буквы, если надо
            r = role_map[lw]
            return r.capitalize() if w[:1].isupper() else r

        # фамилии/слова на -ко обычно не меняем
        if lw.endswith("ко"):
            return w

        # самые частые окончания
        if lw.endswith("а"):
            return w[:-1] + ("и" if w[-1] == "а" else w[-1])
        if lw.endswith("я"):
            return w[:-1] + "ї"
        if lw.endswith("й"):
            return w[:-1] + "я"
        if lw.endswith("ь"):
            return w[:-1] + "я"
        if lw.endswith("о"):
            return w[:-1] + "а"

        # “Петров/Іванов/…” → Петрова/Іванова (простое правило)
        if lw.endswith("ов") or lw.endswith("ев") or lw.endswith("єв") or lw.endswith("ін"):
            return w + "а"

        # по умолчанию для мужских имён на согласную: + "а"
        return w + "а"

    # склоняем все слова (и “мама”, и имя после неё)
    inflected = [inflect_word(w) for w in words]
    return " ".join(inflected)

