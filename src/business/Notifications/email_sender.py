"""
Низкоуровневая отправка email-уведомлений через SMTP.
Использует SSL-подключение (порт 465) для Яндекс-почты.
"""

import smtplib
import ssl
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

from settings import (
    EMAIL_ENABLED,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USE_SSL,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_FROM,
    EMAIL_FROM_NAME,
    EMAIL_RECIPIENTS,
)

logger = logging.getLogger(__name__)


def send_email_notification(subject: str, html_body: str) -> dict:
    """
    Отправляет HTML-письмо всем получателям из EMAIL_RECIPIENTS.

    Args:
        subject: Тема письма
        html_body: HTML-содержимое письма

    Returns:
        dict с ключами: success (bool), message (str), details (list)
    """
    if not EMAIL_ENABLED:
        logger.info("Email-уведомления отключены (EMAIL_ENABLED=false)")
        return {"success": False, "message": "Email отключён", "details": []}

    if not EMAIL_RECIPIENTS:
        logger.warning("Список получателей EMAIL_RECIPIENTS пуст")
        return {"success": False, "message": "Нет получателей", "details": []}

    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        logger.warning("Не указаны EMAIL_USERNAME или EMAIL_PASSWORD")
        return {"success": False, "message": "Не указаны учётные данные SMTP", "details": []}

    max_retries = 3
    details = []

    for recipient in EMAIL_RECIPIENTS:
        success = False
        last_error = ""

        for attempt in range(1, max_retries + 1):
            try:
                # Формируем письмо
                msg = MIMEMultipart("alternative")
                msg["Subject"] = str(Header(subject, 'utf-8'))
                msg["From"] = formataddr((str(Header(EMAIL_FROM_NAME, 'utf-8')), EMAIL_FROM))
                msg["To"] = recipient

                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

                # Отправляем через SSL (порт 465)
                if EMAIL_USE_SSL:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as server:
                        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                        server.sendmail(EMAIL_FROM, recipient, msg.as_string())
                else:
                    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                        server.starttls()
                        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                        server.sendmail(EMAIL_FROM, recipient, msg.as_string())

                logger.info(f"Письмо успешно отправлено на {recipient}")
                details.append({"recipient": recipient, "success": True, "attempt": attempt})
                success = True
                break

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Попытка {attempt}/{max_retries} отправки на {recipient} не удалась: {last_error}"
                )
                if attempt < max_retries:
                    time.sleep(2 * attempt)  # Экспоненциальная задержка

        if not success:
            logger.error(f"Не удалось отправить письмо на {recipient} после {max_retries} попыток: {last_error}")
            details.append({"recipient": recipient, "success": False, "error": last_error})

    all_success = all(d["success"] for d in details)
    return {
        "success": all_success,
        "message": "Все письма отправлены" if all_success else "Часть писем не отправлена",
        "details": details,
    }
