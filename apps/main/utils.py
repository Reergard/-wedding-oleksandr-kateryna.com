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

