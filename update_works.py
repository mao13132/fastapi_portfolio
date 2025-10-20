# ---------------------------------------------
# Program by @developer_telegrams
#
# Скрипт для обновления работ в базе данных
# Version   Date        Info
# 1.0       2024    Initial Version
#
# ---------------------------------------------
import asyncio
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from settings import SQL_URL
from src.sql.bd import async_session_maker, engine
from src.business.Works.works_table import Works
from src.start_data.bad_works_ import works_list
from src.utils._logger import logger_msg


async def update_works_by_slug():
    """
    Обновляет работы в базе данных по slug из списка works_list.
    Обновляет поля: title, text, short_text, descriptions
    """
    print("🚀 Запуск скрипта обновления работ...")

    # Счетчики для статистики
    updated_count = 0
    not_found_count = 0
    error_count = 0

    try:
        async with async_session_maker() as session:
            # Проходим по каждой работе из списка
            for work_data in works_list:
                try:
                    # Получаем slug из данных
                    slug = work_data.get('slug')
                    if not slug:
                        print(f"⚠️  Пропущена работа без slug: {work_data.get('title', 'Без названия')}")
                        continue

                    # Подготавливаем данные для обновления
                    update_data = {
                        'title': work_data.get('title'),
                        'text': work_data.get('text'),
                        'short_text': work_data.get('short_text'),
                        'descriptions': work_data.get('descriptions')
                    }

                    # Удаляем None значения
                    update_data = {k: v for k, v in update_data.items() if v is not None}

                    if not update_data:
                        print(f"⚠️  Нет данных для обновления работы с slug: {slug}")
                        continue

                    # Выполняем обновление
                    query = update(Works).where(Works.slug == slug).values(**update_data)
                    result = await session.execute(query)

                    # Проверяем, была ли обновлена запись
                    if result.rowcount > 0:
                        updated_count += 1
                        print(f"✅ Обновлена работа: {slug} ({work_data.get('title', 'Без названия')})")

                        # Логируем успешное обновление
                        await logger_msg(f"Обновлена работа с slug: {slug}", push=False)
                    else:
                        not_found_count += 1
                        print(f"❌ Работа не найдена в БД: {slug}")

                except Exception as work_error:
                    error_count += 1
                    print(f"❌ Ошибка при обновлении работы {work_data.get('slug', 'unknown')}: {work_error}")
                    await logger_msg(f"Ошибка при обновлении работы {work_data.get('slug', 'unknown')}: {work_error}",
                                     push=True)

            # Коммитим все изменения
            await session.commit()

    except Exception as e:
        print(f"❌ Критическая ошибка при работе с базой данных: {e}")
        await logger_msg(f"Критическая ошибка в update_works_by_slug: {e}", push=True)
        return False

    # Выводим статистику
    print("\n📊 СТАТИСТИКА ОБНОВЛЕНИЯ:")
    print(f"✅ Обновлено работ: {updated_count}")
    print(f"❌ Не найдено в БД: {not_found_count}")
    print(f"⚠️  Ошибок: {error_count}")
    print(f"📝 Всего обработано: {len(works_list)}")

    if updated_count > 0:
        print(f"\n🎉 Успешно обновлено {updated_count} работ в базе данных!")
    else:
        print("\n⚠️  Ни одна работа не была обновлена.")

    return True


async def main():
    """
    Главная функция скрипта
    """
    print("=" * 60)
    print("🔄 СКРИПТ ОБНОВЛЕНИЯ РАБОТ В БАЗЕ ДАННЫХ")
    print("=" * 60)

    try:
        # Проверяем подключение к базе данных
        print(f"🔗 Подключение к БД: {SQL_URL[:20]}...")

        # Запускаем обновление
        success = await update_works_by_slug()

        if success:
            print("\n✅ Скрипт завершен успешно!")
        else:
            print("\n❌ Скрипт завершен с ошибками!")

    except Exception as e:
        print(f"\n💥 Критическая ошибка скрипта: {e}")
        await logger_msg(f"Критическая ошибка в main: {e}", push=True)

    print("=" * 60)


if __name__ == "__main__":
    """
    Точка входа в скрипт
    Запускается только при прямом вызове файла
    """
    # Запускаем асинхронную функцию
    asyncio.run(main())
