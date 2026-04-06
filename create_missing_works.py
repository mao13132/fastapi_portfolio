# ---------------------------------------------
# Program by @developer_telegrams
#
# Скрипт для создания отсутствующих работ в базе данных
# Version   Date        Info
# 1.0       2024    Initial Version
#
# ---------------------------------------------
import asyncio
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from settings import SQL_URL
from src.sql.bd import async_session_maker, engine
from src.business.Works.works_table import Works
from src.start_data.bad_works_ import works_list
from src.utils._logger import logger_msg


async def create_missing_works():
    """
    Создает новые работы в базе данных для тех slug, которые не найдены.
    Добавляет все поля из данных works_list.
    """
    print("🚀 Запуск скрипта создания отсутствующих работ...")
    
    # Счетчики для статистики
    created_count = 0
    existing_count = 0
    error_count = 0
    skipped_count = 0
    
    try:
        async with async_session_maker() as session:
            # Получаем все существующие slug из базы данных
            existing_slugs_query = select(Works.slug)
            existing_slugs_result = await session.execute(existing_slugs_query)
            existing_slugs = {row[0] for row in existing_slugs_result.fetchall()}
            
            print(f"📊 Найдено {len(existing_slugs)} существующих работ в БД")
            print(f"📝 Всего работ в списке: {len(works_list)}")
            
            # Проходим по каждой работе из списка
            for work_data in works_list:
                try:
                    # Получаем slug из данных
                    slug = work_data.get('slug')
                    if not slug:
                        skipped_count += 1
                        print(f"⚠️  Пропущена работа без slug: {work_data.get('title', 'Без названия')}")
                        continue
                    
                    # Проверяем, существует ли уже работа с таким slug
                    if slug in existing_slugs:
                        existing_count += 1
                        print(f"ℹ️  Работа уже существует: {slug} ({work_data.get('title', 'Без названия')})")
                        continue
                    
                    # Подготавливаем данные для создания новой записи
                    # Обязательные поля
                    create_data = {
                        'title': work_data.get('title', 'Без названия'),
                        'text': work_data.get('text', ''),
                        'short_text': work_data.get('short_text', ''),
                        'descriptions': work_data.get('descriptions', ''),
                        'slug': slug,
                        'video': work_data.get('video', ''),  # Обязательное поле
                    }
                    
                    # Дополнительные поля (необязательные)
                    optional_fields = {
                        'sort_id': work_data.get('sort_id'),
                        'image': work_data.get('image'),
                        'views': work_data.get('views', 0)
                    }
                    
                    # Добавляем необязательные поля, если они есть
                    for field, value in optional_fields.items():
                        if value is not None:
                            create_data[field] = value
                    
                    # Проверяем обязательные поля
                    required_fields = ['title', 'text', 'short_text', 'descriptions', 'slug', 'video']
                    missing_fields = [field for field in required_fields if not create_data.get(field)]
                    
                    if missing_fields:
                        error_count += 1
                        print(f"❌ Пропущена работа {slug}: отсутствуют обязательные поля: {missing_fields}")
                        await logger_msg(f"Пропущена работа {slug}: отсутствуют поля {missing_fields}", push=False)
                        continue
                    
                    # Создаем новую запись
                    query = insert(Works).values(**create_data)
                    await session.execute(query)
                    
                    created_count += 1
                    print(f"✅ Создана новая работа: {slug} ({create_data['title']})")
                    
                    # Логируем успешное создание
                    await logger_msg(f"Создана новая работа с slug: {slug}", push=False)
                    
                except Exception as work_error:
                    error_count += 1
                    print(f"❌ Ошибка при создании работы {work_data.get('slug', 'unknown')}: {work_error}")
                    await logger_msg(f"Ошибка при создании работы {work_data.get('slug', 'unknown')}: {work_error}", push=True)
            
            # Коммитим все изменения
            if created_count > 0:
                await session.commit()
                print(f"\n💾 Все изменения сохранены в базе данных")
            
    except Exception as e:
        print(f"❌ Критическая ошибка при работе с базой данных: {e}")
        await logger_msg(f"Критическая ошибка в create_missing_works: {e}", push=True)
        return False
    
    # Выводим статистику
    print("\n📊 СТАТИСТИКА СОЗДАНИЯ:")
    print(f"✅ Создано новых работ: {created_count}")
    print(f"ℹ️  Уже существовало: {existing_count}")
    print(f"⚠️  Пропущено (нет slug): {skipped_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📝 Всего обработано: {len(works_list)}")
    
    if created_count > 0:
        print(f"\n🎉 Успешно создано {created_count} новых работ в базе данных!")
    elif existing_count == len(works_list) - skipped_count - error_count:
        print("\n✅ Все работы уже существуют в базе данных!")
    else:
        print("\n⚠️  Не удалось создать новые работы.")
    
    return True


async def validate_work_data(work_data: dict) -> tuple[bool, list]:
    """
    Валидирует данные работы перед созданием.
    
    Args:
        work_data: Словарь с данными работы
        
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    # Проверяем обязательные поля
    required_fields = {
        'slug': 'Уникальный идентификатор',
        'title': 'Название работы',
        'text': 'Полное описание',
        'short_text': 'Краткое описание',
        'descriptions': 'Описания',
        'video': 'Видео'
    }
    
    for field, description in required_fields.items():
        value = work_data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            errors.append(f"Отсутствует {description} ({field})")
    
    # Проверяем типы данных
    if work_data.get('sort_id') is not None:
        try:
            int(work_data['sort_id'])
        except (ValueError, TypeError):
            errors.append("sort_id должно быть числом")
    
    if work_data.get('views') is not None:
        try:
            int(work_data['views'])
        except (ValueError, TypeError):
            errors.append("views должно быть числом")
    
    # Проверяем длину slug (должен быть уникальным и не слишком длинным)
    slug = work_data.get('slug', '')
    if len(slug) > 100:
        errors.append("slug слишком длинный (максимум 100 символов)")
    
    return len(errors) == 0, errors


async def main():
    """
    Главная функция скрипта
    """
    print("=" * 70)
    print("🆕 СКРИПТ СОЗДАНИЯ ОТСУТСТВУЮЩИХ РАБОТ В БАЗЕ ДАННЫХ")
    print("=" * 70)
    
    try:
        # Проверяем подключение к базе данных
        print(f"🔗 Подключение к БД: {SQL_URL[:20]}...")
        
        # Запускаем создание отсутствующих работ
        success = await create_missing_works()
        
        if success:
            print("\n✅ Скрипт завершен успешно!")
        else:
            print("\n❌ Скрипт завершен с ошибками!")
            
    except Exception as e:
        print(f"\n💥 Критическая ошибка скрипта: {e}")
        await logger_msg(f"Критическая ошибка в main: {e}", push=True)
    
    print("=" * 70)


if __name__ == "__main__":
    """
    Точка входа в скрипт
    Запускается только при прямом вызове файла
    """
    # Запускаем асинхронную функцию
    asyncio.run(main())