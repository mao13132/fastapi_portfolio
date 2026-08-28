"""
HTML-шаблоны email-уведомлений.
"""

from datetime import datetime


def _base_wrapper(title: str, content: str, color: str = "#2563eb") -> str:
    """
    Общая обёртка для всех email-шаблонов.

    Args:
        title: Заголовок письма
        content: HTML-содержимое (тело письма)
        color: Цвет акцента (по умолчанию синий)

    Returns:
        Полный HTML-документ
    """
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f4f7; font-family: Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                        <!-- Header -->
                        <tr>
                            <td style="background-color:{color}; padding:20px 30px; text-align:center;">
                                <h1 style="color:#ffffff; margin:0; font-size:20px;">{title}</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding:30px;">
                                {content}
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color:#f9fafb; padding:15px 30px; text-align:center; border-top:1px solid #e5e7eb;">
                                <p style="color:#9ca3af; font-size:12px; margin:0;">
                                    Уведомление отправлено автоматически — {now}
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def _field_row(label: str, value: str) -> str:
    """
    Строка таблицы с меткой и значением.

    Args:
        label: Название поля
        value: Значение поля

    Returns:
        HTML-строка таблицы
    """
    return f"""
    <tr>
        <td style="padding:10px 15px; border-bottom:1px solid #e5e7eb; font-weight:bold; color:#374151; width:35%; vertical-align:top;">
            {label}
        </td>
        <td style="padding:10px 15px; border-bottom:1px solid #e5e7eb; color:#111827;">
            {value or "—"}
        </td>
    </tr>
    """


def render_order_email(
    type_order: str,
    name: str,
    phone: str,
    telegram: str = None,
    text: str = None,
    ip: str = None,
) -> str:
    """
    Шаблон письма для новой заявки.

    Args:
        type_order: Тип заявки (например, "Контактная форма", "Квиз")
        name: Имя клиента
        phone: Телефон клиента
        telegram: Telegram клиента (опционально)
        text: Текст сообщения (опционально)
        ip: IP-адрес клиента (опционально)

    Returns:
        Полный HTML-документ
    """
    rows = ""
    rows += _field_row("📋 Тип заявки", type_order)
    rows += _field_row("👤 Имя", name)
    rows += _field_row("📞 Телефон", phone)

    if telegram:
        rows += _field_row("✈️ Telegram", telegram)
    if text:
        rows += _field_row("💬 Сообщение", text)
    if ip:
        rows += _field_row("🌐 IP-адрес", ip)

    content = f"""
    <p style="color:#374151; font-size:15px; margin:0 0 20px 0;">
        Поступила новая заявка на сайте!
    </p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb; border-radius:6px; overflow:hidden;">
        {rows}
    </table>
    """

    return _base_wrapper("📬 Новая заявка", content, color="#2563eb")


def render_quiz_email(answers: dict, ip: str = None) -> str:
    """
    Шаблон письма для результатов опросника (квиза).

    Args:
        answers: Словарь с ответами {вопрос: ответ}
        ip: IP-адрес клиента (опционально)

    Returns:
        Полный HTML-документ
    """
    rows = ""
    for question, answer in answers.items():
        rows += _field_row(question, str(answer))

    if ip:
        rows += _field_row("🌐 IP-адрес", ip)

    content = f"""
    <p style="color:#374151; font-size:15px; margin:0 0 20px 0;">
        Пользователь прошёл опросник на сайте!
    </p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb; border-radius:6px; overflow:hidden;">
        {rows}
    </table>
    """

    return _base_wrapper("📊 Результаты опросника", content, color="#059669")
