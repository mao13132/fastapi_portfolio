### Точное руководство: Как подключать кастомные шаблоны в `sqladmin`

Вот пошаговая инструкция, основанная на нашем успешном опыте. Сохраните ее, она вам пригодится.

#### Шаг 1: Создайте файл шаблона

1.  **Где:** В папке `templates/sqladmin/`. Это важно, `sqladmin` ищет шаблоны именно там.
2.  **Название:** Дайте ему осмысленное имя. Например, `bike_list.html` (для списка велосипедов) или `user_details.html` (для деталей пользователя).

#### Шаг 2: Наполните шаблон (Надежный метод "Все в одном")

Откройте ваш новый файл и вставьте в него этот код-каркас. Он уже содержит все необходимое.

```html
{% extends "sqladmin/list.html" %}

{#
   ВАЖНО: Вместо "sqladmin/list.html" вы можете использовать:
   - "sqladmin/create.html" (для страницы создания)
   - "sqladmin/edit.html" (для страницы редактирования)
   - "sqladmin/details.html" (для страницы деталей)
#}


{# Блок для встраивания CSS-стилей #}
{% block head %}
    {{ super() }}  {# Эта строка ОБЯЗАТЕЛЬНА! Она загружает стили самой админки. #}
    <style>
        /*
         * ВАШИ CSS-СТИЛИ ЗДЕСЬ
         */
        .my-custom-class {
            color: red;
        }
    </style>
{% endblock %}


{# Блок для встраивания JavaScript-кода #}
{% block tail %}
    {{ super() }}  {# Эта строка ОБЯЗАТЕЛЬНА! Она загружает скрипты самой админки. #}
    <script>
        // Самовызывающаяся функция для изоляции кода
        (function() {
            /*
             * ВАШ JAVASCRIPT-КОД ЗДЕСЬ
             */
            console.log("Кастомный скрипт загружен!");
        })();
    </script>
{% endblock %}

```

#### Шаг 3: Подключите шаблон в файле `..._admin.py`

Откройте нужный файл администратора (например, `src/admin/views/bike_admin.py`) и укажите путь к вашему новому шаблону с помощью специального атрибута класса.

*   Для страницы **списка**: `list_template`
*   Для страницы **создания**: `create_template`
*   Для страницы **редактирования**: `edit_template`
*   Для страницы **деталей**: `details_template`

**Пример:**

```python
# В файле src/admin/views/bike_admin.py

from sqladmin import ModelView
from src.sql.models import Bikes

class BikeAdmin(ModelView, model=Bikes):
    # ...
    # все ваши обычные настройки (column_list, form_labels и т.д.)
    # ...

    # --- ПОДКЛЮЧЕНИЕ КАСТОМНОГО ШАБЛОНА ---
    # Указываем, что для страницы списка нужно использовать наш файл.
    list_template = "sqladmin/bike_list.html"

```

---

### Проблема: Сохранение существующих файлов при редактировании

При редактировании записи с полями `FileType` (например, изображениями), если не загружать новый файл, `sqladmin` может удалить старый. Это происходит потому, что пустое поле в форме интерпретируется как намерение очистить значение.

#### Решение: Переопределить `update_model`

Чтобы избежать потери данных, нужно переопределить метод `update_model` в вашем классе `ModelView` и вручную контролировать обновление файловых полей.

**Ключевая логика:** Обновлять поле с файлом нужно только в том случае, если был загружен **действительно новый файл**. Новый файл, в отличие от "пустышки", представляющей старое значение, всегда имеет атрибут `size`, который больше нуля.

#### Пример реализации:

```python
# В файле .../admin/views/my_model_admin.py

from typing import Any
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqladmin import ModelView
from starlette.datastructures import UploadFile

# ... импорт вашей модели

class MyModelAdmin(ModelView, model=MyModel):
    # ... ваши обычные настройки ...

    async def update_model(self, request: Request, pk: Any, data: dict) -> Any:
        """
        Переопределяем метод обновления, чтобы не удалять существующие файлы,
        если новые не были загружены.
        """
        engine = request.scope['endpoint'].__self__.engine
        async with AsyncSession(engine) as session:
            # 1. Получаем объект из БД
            model = await session.get(self.model, int(pk))

            # 2. Извлекаем данные о файлах из формы.
            #    ВАЖНО: 'my_image_field' - это имя вашего поля в модели.
            image_data = data.pop('my_image_field', None)

            # 3. Обновляем остальные поля (текст, числа, булевы значения и т.д.)
            for key, value in data.items():
                setattr(model, key, value)

            # 4. Обновляем файл, только если он был ДЕЙСТВИТЕЛЬНО загружен.
            #    Ключевая проверка: у нового файла есть размер (size > 0).
            #    У "пустого" файла, который представляет старое значение, размер будет None.
            if isinstance(image_data, UploadFile) and image_data.size is not None and image_data.size > 0:
                model.my_image_field = image_data

            # 5. Сохраняем все изменения
            session.add(model)
            await session.commit()
            await session.refresh(model)

            return model

```
Этот метод гарантирует, что существующие файлы останутся нетронутыми, если вы их не меняли при редактировании записи.

---

### Создание кастомной страницы без модели (BaseView)

Когда нужна страница статистики, дашборд или другая функциональность **без привязки к модели**, используйте `BaseView`.

#### Ситуация

Требуется страница в админ-панели для отображения статистики:
- Всего пользователей
- Активных сегодня
- Оборота и т.д.

Это не CRUD-операция над моделью, а просто страница с данными из разных моделей.

#### Ошибки и решения

**Ошибка 1: AttributeError: 'StatisticsAdmin' object has no attribute 'model'**

```python
# НЕПРАВИЛЬНО - ModelView требует model=
class StatisticsAdmin(ModelView):
    ...
```

```python
# ПРАВИЛЬНО - BaseView для страниц без модели
from sqladmin import BaseView, expose
class StatisticsAdmin(BaseView):
    ...
```

**Ошибка 2: ImportError: cannot import name 'async_session'**

```python
# НЕПРАВИЛЬНО - такого имени нет
from src.core.database import async_session
```

```python
# ПРАВИЛЬНО - используйте async_session_maker
from src.core.database import async_session_maker
```

**Ошибка 3: Не добавляется маршрут**

```python
# НЕПРАВИЛЬНО - атрибут route не работает
class StatisticsAdmin(BaseView):
    route = "/admin/statistics"
```

```python
# ПРАВИЛЬНО - используйте декоратор @expose
class StatisticsAdmin(BaseView):
    @expose("/statistics", methods=["GET"])
    async def statistics_page(self, request: Request):
        ...
```

**Ошибка 4: TypeError: unhashable type: 'dict' в TemplateResponse**

```python
# НЕПРАВИЛЬНО - неправильный порядок параметров
return await self.templates.TemplateResponse(
    "sqladmin/statistics.html",
    {"request": request, "stats": stats},
)
```

```python
# ПРАВИЛЬНО - сначала request, потом шаблон, потом контекст
return await self.templates.TemplateResponse(
    request,
    "sqladmin/statistics.html",
    {"request": request, "stats": stats},
)
```

#### Пример реализации

**1. Сервис для статистики** (`src/domains/statistics/services/statistics_service.py`):

```python
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.user import User
from src.database.models.payment import Payment
from src.database.models.subscription import Subscription
from src.database.models.payment_statuses import PAYMENT_STATUS_SUCCEEDED
from src.database.models.subscription_statuses import SUBSCRIPTION_ACTIVE

class StatisticsService:
    session: AsyncSession

    async def get_total_users(self) -> int:
        query = select(func.count(User.id))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_all_stats(self) -> dict:
        return {
            "total_users": await self.get_total_users(),
            # ... другие метрики
        }
```

**2. Админ View** (`src/admin/views/statistics.py`):

```python
from fastapi import Request
from sqladmin import BaseView, expose
from src.domains.statistics.services import StatisticsService
from src.core.database import async_session_maker

class StatisticsAdmin(BaseView):
    name = "Статистика"
    icon = "fa-solid fa-chart-line"

    @expose("/statistics", methods=["GET"])
    async def statistics_page(self, request: Request):
        stats = {}
        async with async_session_maker() as session:
            service = StatisticsService()
            service.session = session
            stats = await service.get_all_stats()

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/statistics.html",
            {"request": request, "stats": stats},
        )
```

**3. Шаблон** (`templates/sqladmin/statistics.html`):

```html
{% extends "sqladmin/layout.html" %}

{% block content %}
<div class="stats-container">
    <h1 class="h3 mb-4 text-gray-800">📊 Статистика системы</h1>
    <div class="row">
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-left-primary shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-primary">Всего пользователей</div>
                    <div class="h5 mb-0 font-weight-bold">{{ stats.total_users }}</div>
                </div>
            </div>
        </div>
        <!-- другие карточки статистики -->
    </div>
</div>
{% endblock %}
```

**4. Подключение в main.py**:

```python
from src.admin.views.statistics import StatisticsAdmin
# ...
admin.add_view(StatisticsAdmin)
```

#### Ключевые моменты

1. Для страниц **без модели** используйте `BaseView`, не `ModelView`
2. Маршрут задается через декоратор `@expose("/path", methods=["GET", "POST"])`
3. `TemplateResponse` принимает параметры в порядке: `request`, `template_name`, `context`
4. Для работы с БД используйте `async_session_maker()`, не `async_session`

---

### ОБЪЕДИНЕНИЕ GET И POST В ОДИН ENDPOINT (GET страница + POST действия)

Это критически важно для случаев, когда на одной странице нужна и загрузка файлов, и управление данными (например, загрузка tdata + управление аккаунтами).

#### Проблема с routing в BaseView

**Симптомы:**
- Sidebar показывает неправильный URL (например, `/admin/account-action` вместо `/admin/upload`)
- Первый `@expose` в файле определяет URL sidebar, даже если это POST метод
- `identity` атрибут класса НЕ работает для sidebar - SQLAdmin использует имя первого метода с `@expose`

**Решение:** Объединить GET и POST в один `@expose` endpoint

```python
class MyPageAdmin(BaseView):
    name = "Моя страница"
    icon = "fa-solid fa-file"

    # Единый endpoint для GET (страница) и POST (действия)
    @expose("/my-page", methods=["GET", "POST"])
    async def my_page(self, request: Request):
        # GET - показать страницу
        if request.method == "GET":
            return await self.templates.TemplateResponse(
                request,
                "sqladmin/my_page.html",
                {"request": request}
            )

        # POST - обработать действие
        form = await request.form()
        action = form.get("action")

        if action == "delete":
            # ... логика удаления
            return JSONResponse({"status": "success", "message": "Удалено"})
        elif action == "update":
            # ... логика обновления
            return JSONResponse({"status": "success", "message": "Обновлено"})

        return JSONResponse({"status": "error", "message": "Неизвестное действие"})
```

**JavaScript (все запросы на один endpoint):**

```javascript
// Загрузка страницы - GET /admin/my-page
// Управление действиями - POST /admin/my-page

async function deleteItem(id) {
    const formData = new FormData();
    formData.append('action', 'delete');
    formData.append('id_pk', id);

    const response = await fetch('/admin/my-page', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    if (result.status === 'success') {
        location.reload();
    } else {
        alert('Ошибка: ' + result.message);
    }
}
```

#### Почему это работает

1. **Sidebar URL** - используется ПЕРВЫЙ `@expose` в файле. Если это `methods=["GET", "POST"]`, то sidebar показывает правильный URL
2. **GET запросы** - отдают HTML страницу
3. **POST запросы** - различаются по наличию параметра `action`:
   - Если есть `action` → управление данными (AJAX)
   - Если нет `action` → загрузка файлов или другая логика

---

### ВАЖНО: Всегда возвращайте JSONResponse, а не dict

При использовании `BaseView` и возврате JSON данных из POST методов, вы должны использовать `JSONResponse`:

```python
# ПРАВИЛЬНО
return JSONResponse({"status": "success", "message": "Удалено"})

# НЕПРАВИЛЬНО - вызовет TypeError: 'dict' object is not callable
return {"status": "success", "message": "Удалено"}
```

SQLAdmin/FastAPI требует явного создания объекта ответа.

---

### Практический пример: Загрузка файлов + управление аккаунтами

Полный рабочий пример (`src/pyrogram/tdata_admin.py`):

```python
from fastapi import Request
from sqladmin import BaseView, expose
from starlette.responses import JSONResponse
import os
import uuid
import logging

logger = logging.getLogger(__name__)

TDATA_STORAGE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'tdata_storage')


class TdataUploadAdmin(BaseView):
    name = "Загрузка tdata"
    icon = "fa-solid fa-folder-plus"

    # Единый endpoint для GET (страница) и POST (загрузка + действия)
    @expose("/upload", methods=["GET", "POST"])
    async def upload_page(self, request: Request):
        from src.sql.accounts import AccountStatus

        # GET - показать страницу
        if request.method == "GET":
            try:
                db = BotDB()
                accounts = await db.accounts.get_all()
            except Exception as e:
                logger.error(f"Ошибка загрузки аккаунтов: {e}")
                accounts = []

            return await self.templates.TemplateResponse(
                request,
                "sqladmin/tdata_upload.html",
                {
                    "request": request,
                    "accounts": accounts,
                    "AccountStatus": AccountStatus
                }
            )

        # POST - обработать действие или загрузку
        try:
            form = await request.form()
            action = form.get("action")

            # Если есть action - управление аккаунтом
            if action:
                return await self._handle_account_action(form, action)

            # Иначе - загрузка файлов
            return await self._handle_file_upload(form)

        except Exception as e:
            logger.error(f"Error in upload_page: {e}", exc_info=True)
            return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

    async def _handle_account_action(self, form, action):
        """Обработка действий с аккаунтами"""
        try:
            id_pk = int(form.get("id_pk"))
            db = BotDB()

            if action == "delete":
                account = await db.accounts.get_by_id(id_pk)
                if not account:
                    return JSONResponse({"status": "error", "message": "Аккаунт не найден"}, status_code=404)

                if account.is_active:
                    await db.accounts.set_active(id_pk, False)

                tdata_path = account.tdata_path
                if tdata_path and os.path.exists(tdata_path):
                    import shutil
                    shutil.rmtree(tdata_path)

                await db.accounts.delete_account(id_pk)
                return JSONResponse({"status": "success", "message": "Аккаунт удалён"})

            elif action == "set_active":
                await db.accounts.set_active(id_pk, True)
                return JSONResponse({"status": "success", "message": "Аккаунт активирован"})

            elif action == "unset_active":
                await db.accounts.set_active(id_pk, False)
                return JSONResponse({"status": "success", "message": "Аккаунт деактивирован"})

            elif action == "authorize":
                await db.accounts.set_authorized(id_pk, True)
                return JSONResponse({"status": "success", "message": "Аккаунт авторизован"})

            else:
                return JSONResponse({"status": "error", "message": "Неизвестное действие"}, status_code=400)

        except Exception as e:
            logger.error(f"Ошибка _handle_account_action: {e}", exc_info=True)
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    async def _handle_file_upload(self, form):
        """Обработка загрузки файлов tdata"""
        try:
            files = form.getlist("files")
            folder_name = form.get("folder_name", None)

            unique_id = uuid.uuid4().hex[:8]
            session_name = f"{folder_name}_{unique_id}" if folder_name else f"session_{unique_id}"

            session_path = os.path.join(TDATA_STORAGE_PATH, session_name)
            os.makedirs(session_path, exist_ok=True)

            for file in files:
                if file.size and file.size > 0:
                    file_path = os.path.join(session_path, file.filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "wb") as buffer:
                        buffer.write(await file.read())

            # Создать запись в БД и запустить обработку
            await self._create_account_record(session_name, session_path)

            import asyncio
            asyncio.create_task(asyncio.to_thread(process_tdata_session, session_path, session_name))

            return JSONResponse({"status": "success", "message": "Загрузка началась"})

        except Exception as e:
            logger.error(f"Error in _handle_file_upload: {e}", exc_info=True)
            return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
```

**JavaScript часть:**

```javascript
// Все запросы идут на один endpoint /admin/upload

async function setActive(id) {
    const formData = new FormData();
    formData.append('action', 'set_active');
    formData.append('id_pk', id);

    const response = await fetch('/admin/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    if (result.status === 'success') {
        location.reload();
    } else {
        alert('Ошибка: ' + result.message);
    }
}

async function deleteAccount(id) {
    if (!confirm('Удалить аккаунт #' + id + '?')) return;

    const formData = new FormData();
    formData.append('action', 'delete');
    formData.append('id_pk', id);

    const response = await fetch('/admin/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    if (result.status === 'success') {
        document.getElementById('account-' + id).remove();
    } else {
        alert('Ошибка: ' + result.message);
    }
}

// Загрузка файлов
async function uploadFiles(files) {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }
    formData.append('folder_name', 'myfolder');

    const response = await fetch('/admin/upload', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}
```

**HTML кнопки:**

```html
<button onclick="setActive('{{ account.id_pk }}')">Активировать</button>
<button onclick="deleteAccount('{{ account.id_pk }}')">Удалить</button>
```

**Подключение:**

```python
# В main.py
from src.pyrogram.tdata_admin import TdataUploadAdmin

admin.add_view(TdataUploadAdmin)
```

---

### Типичные ошибки и решения

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `TypeError: 'dict' object is not callable` | Возврат `dict` вместо `JSONResponse` | Используйте `return JSONResponse({"status": "success"})` |
| 404 на POST endpoint | Неправильный URL в JavaScript | Проверьте URL - используйте тот же что для GET страницы |
| Sidebar показывает неверный URL | Первый `@expose` это POST метод | Объедините GET и POST в один endpoint |
| `TemplateResponse` ошибка | Неправильный порядок параметров | `TemplateResponse(request, "template.html", context)` |

---

### Заключение

При работе с `BaseView` в SQLAdmin:

1. **Объединяйте GET и POST** в один `@expose` endpoint для решения проблем с routing
2. **Всегда используйте `JSONResponse`** для возврата данных в POST
3. **Используйте параметр `action`** для различения типов операций в POST
4. **Следите за порядком методов** - первый `@expose` определяет sidebar URL

---

### Практический баг: 500 на стандартной list page из-за `column_filters`

Ниже важная заметка именно под этот проект. Это не теоретический кейс, а реальная поломка, которая уже была найдена и исправлена.

#### Симптом

Некоторые стандартные `ModelView` страницы SQLAdmin отдавали `500 Internal Server Error`:

- `/admin/showcase-item/list`
- `/admin/media-generation/list`

При этом:

- `BaseView` страницы работали нормально
- данные из БД читались нормально
- `ShowcaseControlAdmin(BaseView)` открывался без ошибок
- проблема проявлялась именно на стандартной `list` странице SQLAdmin

#### Что сначала вводит в заблуждение

Можно легко подумать, что проблема в одном из пунктов ниже:

- сломан `column_formatters`
- проблема в `Markup`
- сломан `column_default_sort`
- проблема в `can_export`
- проблема в auth/session
- проблема в шаблонах проекта

Но в этом кейсе корень был не в них.

#### Реальная причина

В текущем проекте используется `sqladmin==0.23.0` по `backend/requirements.txt`.

В этой версии list page с правым/боковым блоком фильтров ожидает не просто сырые SQLAlchemy колонки в `column_filters`, а **явные filter objects**.

То есть вот такой код может ломать страницу:

```python
column_filters = [
    ShowcaseItem.category_label,
    ShowcaseItem.scenario_kind,
    ShowcaseItem.composer_mode,
    ShowcaseItem.is_featured,
    ShowcaseItem.is_active,
]
```

Потому что шаблон и filter pipeline дальше ждут у каждого фильтра поля и методы уровня:

- `title`
- `parameter_name`
- `has_operator`
- `lookups(...)`
- `get_filtered_query(...)`

У сырой SQLAlchemy колонки этого API нет.

#### Правильный вариант

Нужно использовать объекты фильтров из `sqladmin.filters`.

Пример для строковых и boolean полей:

```python
from sqladmin.filters import AllUniqueStringValuesFilter, BooleanFilter


column_filters = [
    AllUniqueStringValuesFilter(ShowcaseItem.category_label, title="Категория"),
    AllUniqueStringValuesFilter(ShowcaseItem.scenario_kind, title="Тип сценария"),
    AllUniqueStringValuesFilter(ShowcaseItem.composer_mode, title="Режим composer"),
    BooleanFilter(ShowcaseItem.is_featured, title="Featured"),
    BooleanFilter(ShowcaseItem.is_active, title="Активен"),
]
```

Для другой модели:

```python
from sqladmin.filters import AllUniqueStringValuesFilter


column_filters = [
    AllUniqueStringValuesFilter(MediaGeneration.output_kind, title="Output Kind"),
    AllUniqueStringValuesFilter(MediaGeneration.status, title="Статус"),
    AllUniqueStringValuesFilter(MediaGeneration.stage, title="Stage"),
    AllUniqueStringValuesFilter(MediaGeneration.provider, title="Провайдер"),
    AllUniqueStringValuesFilter(MediaGeneration.model_id, title="Модель"),
]
```

#### Как быстро понять, что проблема именно в фильтрах

Если падает `ModelView.list`, а `BaseView` рядом работает, проверь в таком порядке:

1. Есть ли общий паттерн у всех падающих list pages
2. Совпадает ли у них наличие `column_filters`
3. Используются ли там сырые колонки вместо filter objects
4. Какая версия `sqladmin` реально стоит в `venv`

В нашем кейсе очень помогло именно сравнение:

- какие admin pages падают
- какие не падают
- что общего у двух падающих страниц

Оказалось:

- `showcase_item.py` падает
- `media_generation.py` падает
- другие list pages не падают
- у двух падающих страниц общий признак: настроен `column_filters`

Это быстро сузило поиск.

#### Важная ловушка для будущих ИИ

Нельзя доверять только глобальному Python окружению агента.

Реально была такая ситуация:

- в проекте в `requirements.txt` зафиксирован `sqladmin==0.23.0`
- в окружении агента локально стоял другой `sqladmin`
- из-за этого ошибка сначала не воспроизводилась, хотя у пользователя в живом сервере она была

Вывод:

1. сначала проверь версию в `requirements.txt`
2. потом проверь фактическую версию в `venv`
3. не делай вывод "ошибка не воспроизводится" до сверки версий

#### На что смотреть в коде SQLAdmin

Если нужно глубже проверить поведение именно текущей версии SQLAdmin, смотри:

- `sqladmin/templates/sqladmin/list.html`
- `sqladmin/models.py`
- `sqladmin/filters.py`

Особенно важно посмотреть:

- как шаблон рендерит filter sidebar
- что ожидается от элементов `model_view.get_filters()`
- какие filter classes предоставляет сама библиотека

#### Практическое правило для этого проекта

Если в `ModelView` нужен sidebar/filtering, не писать так:

```python
column_filters = [MyModel.some_field]
```

Лучше сразу писать через filter objects:

```python
column_filters = [
    AllUniqueStringValuesFilter(MyModel.some_field, title="Some Field"),
]
```

Для boolean:

```python
column_filters = [
    BooleanFilter(MyModel.is_active, title="Активен"),
]
```

#### Если снова видите `500` на `/admin/.../list`

Мини-чеклист:

1. проверить `column_filters`
2. проверить версию `sqladmin`
3. сравнить с другой рабочей `ModelView`
4. посмотреть, не падают ли ещё 1-2 list pages с похожей конфигурацией
5. не путать проблему `ModelView.list` с проблемами `BaseView`
6. проверить, не воспроизводится ли ошибка только в проектном `venv`

#### Итог по этому багу

- Архитектура `ModelView` для CRUD и `BaseView` для control/dashboard была правильной
- Ошибка была не в самой идее showcase admin
- Ошибка была в version-specific несовместимости `column_filters` с текущим рендерингом SQLAdmin
- Исправление: заменить сырые колонки в `column_filters` на явные filter objects из `sqladmin.filters`

---

### Практический баг: POST успешный, но следующий GET admin-страницы падает

Это универсальный паттерн для любых admin/control/dashboard страниц, а не только для одного проекта.

#### Симптом

Типичный сценарий такой:

1. `GET` admin-страницы открывается нормально
2. `POST` действия проходит успешно
3. сервер отвечает `302` или `303`
4. следующий `GET` этой же страницы падает с `500`

Классический лог-паттерн:

- `GET ... status=200`
- `POST ... status=200/201/302/303`
- следующий `GET ... status=500`

Это значит:

- write path, возможно, уже отработал успешно
- а падает уже повторный read/render path после redirect

#### Что обычно ошибочно подозревают первым

На таком симптоме часто начинают обвинять:

- upload файлов
- multipart parsing
- `request.form()`
- `RedirectResponse`
- сам SQLAdmin
- конкретную POST-логику

Но очень часто корень сидит уже не там.

#### Универсальная реальная причина

POST-запрос создаёт или меняет данные.

После этого следующий `GET` начинает рендерить новые блоки, которые раньше не активировались:

- history
- analytics
- dashboard cards
- derived metrics
- before/after comparison
- impact analysis
- conditional sections, которые показываются только когда данные уже есть

Из-за этого:

- POST может быть успешным
- данные могут реально сохраниться
- а страница ломается только на повторном чтении этих новых данных

#### Главный диагностический принцип

Если:

1. `GET` до действия был `200`
2. `POST` был успешным
3. следующий `GET` упал

то в первую очередь надо подозревать **read path**, а не **write path**.

То есть проверять:

- что именно создал или изменил POST
- какие блоки начинают рендериться только после этого
- какие вычисления завязаны на новых записях

#### Где смотреть в первую очередь

Для любых admin/control/dashboard страниц сначала проверять:

1. loaders
2. aggregate queries
3. history rendering
4. metrics / analytics blocks
5. before/after calculations
6. date math
7. conditional UI branches, которые активируются только при наличии новых данных

Особенно опасны:

- `_load_history(...)`
- `_load_impact_rows(...)`
- `_load_recent_*`
- `_build_*_metrics(...)`
- `_aggregate_*`

#### Частая скрытая причина: timezone-aware vs timezone-naive datetime

Один из самых коварных вариантов:

```python
now = datetime.utcnow()
result = min(now, db_dt + timedelta(days=7))
```

Если:

- `db_dt` пришёл из БД как timezone-aware
- `datetime.utcnow()` создал timezone-naive объект

то Python может упасть с:

```python
TypeError: can't compare offset-naive and offset-aware datetimes
```

#### Почему это коварно

Потому что до появления первой записи всё может работать идеально.

Типичный скрытый механизм:

1. страница без history/analytics работает нормально
2. POST создаёт первую запись
3. повторный GET впервые заходит в новую ветку расчётов
4. только там и проявляется исключение

Визуально кажется:

- "сломали кнопку"
- "сломали upload"
- "сломали SQLAdmin form"

Хотя реально:

- POST уже успешно выполнился
- а упал последующий анализ/рендер данных

#### Универсальный анти-паттерн

Не делать так:

```python
db_dt = entry.created_at
now = datetime.utcnow()
result = min(now, db_dt + timedelta(days=7))
```

Если `db_dt` aware, это потенциально аварийный код.

#### Универсальный безопасный шаблон

Лучше так:

```python
db_dt = entry.created_at
now = datetime.now(db_dt.tzinfo) if db_dt and db_dt.tzinfo else datetime.utcnow()
result = min(now, db_dt + timedelta(days=7))
```

Или ещё лучше:

- заранее договориться, что все сравниваемые datetime в одном timezone-формате
- и не смешивать naive и aware значения внутри одной функции

#### Что обязательно проверить в коде

Если есть:

- `DateTime(timezone=True)`
- `created_at`
- `updated_at`
- временные окна
- retention windows
- impact windows
- `min(...)` / `max(...)` по датам

то обязательно проверить:

1. aware или naive datetime приходит из БД
2. каким способом создаётся `now`
3. не используются ли рядом `datetime.utcnow()` и aware timestamps
4. не появляется ли новая date-math ветка только после первой записи

#### Мини-чеклист для будущих ИИ

Если после POST следующий GET падает:

1. не обвинять сразу upload или form parsing
2. проверить, сохранились ли данные фактически
3. проверить, какие новые блоки теперь начали рендериться
4. пройтись по loaders и derived metrics
5. проверить все операции над датами и временными окнами
6. отдельно искать смешение naive/aware datetime
7. фиксить сразу все аналогичные места, а не только один route

#### Итог

- Успешный POST не означает, что проблема была в нём
- Следующий `GET 500` часто указывает на поломку в analytics/history/render path
- Самые опасные скрытые причины: derived metrics, conditional branches и date math
- При работе с admin/dashboard страницами всегда проверяй не только write path, но и первый read path после redirect



---

## Проблема: как добавить в форму SQLAdmin поле, которого нет в модели (пример - пароль)

**Дата фиксации:** 2026-07-03
**Версия sqladmin:** 0.17.0

### Симптом

При открытии страницы создания/редактирования сущности приложение падает:

```
File ".../sqladmin/forms.py", line 620, in get_model_form
    attributes.append((name, mapper.attrs[name]))
KeyError: 'password'
```

Или при сабмите формы SQLAlchemy пытается сделать `setattr(user, "password", ...)`, а у модели такого атрибута нет (в БД лежит только `password_hash`).

### Причина

В отличие от Flask-Admin, в **SQLAdmin 0.17 нет `form_extra_fields`**. Этот параметр молча игнорируется.

Всё, что перечислено в `form_columns`, конвертер ищет в `mapper.attrs[...]` SQLAlchemy-модели. Если положить туда виртуальное поле (например, `password`) - `KeyError`.

Аналогично `form_overrides` работает только для существующих колонок модели: он подменяет тип поля, а не добавляет новое.

### Правильное решение (best practice для SQLAdmin)

Правило: **виртуальные поля добавляются через переопределение `scaffold_form()`**, а не через `form_columns`.

Пошагово:

1. В `form_columns` оставляем **только реальные атрибуты модели** (колонки и relationships).
2. Переопределяем `async def scaffold_form(self)` - берем стандартную форму от `super()` и подмешиваем туда WTForms-поле.
3. В `on_model_change(data, ...)` первым делом делаем `data.pop("<virtual_field>", None)`, чтобы SQLAlchemy не попытался сделать `setattr(model, "password", ...)`.
4. Валидацию `Required` при create ставим **не в форме**, а в `on_model_change` (форма одна для create и edit; на форме используем `validators.Optional()`).

### Рабочий пример: пароль пользователя

```python
from sqladmin import ModelView
from wtforms import PasswordField, validators

from app.auth.hash_password import hash_password
from app.database import models


class UserAdmin(ModelView, model=models.User):
    # 1. Только реальные поля модели. Никакого "password" здесь!
    form_columns = [
        "username",
        "role",
        "is_active",
        "is_superadmin",
        "bundles",
        "places",
    ]

    async def scaffold_form(self):
        """Добавляет виртуальное поле пароля в стандартную форму SQLAdmin."""
        # 1. Берем готовую форму, сгенерированную SQLAdmin по form_columns.
        form_class = await super().scaffold_form()

        # 2. Optional() - потому что при редактировании пустое поле = "не менять пароль".
        # Обязательность при создании проверим в on_model_change.
        form_class.password = PasswordField(
            "Пароль",
            description="Обязательно при создании. При редактировании оставьте пустым, чтобы не менять.",
            validators=[validators.Optional()],
        )
        return form_class

    async def on_model_change(self, data, model, is_created, request):
        """Хеширует пароль перед сохранением и удаляет его из data."""
        # 1. КРИТИЧНО: pop, а не get. Иначе SQLAlchemy сделает setattr(user, "password", ...) и упадет.
        raw_password = (data.pop("password", None) or "").strip()

        if is_created:
            # 2. При создании пароль обязателен.
            if not raw_password:
                raise ValueError("Пароль обязателен при создании пользователя")
            model.password_hash = hash_password(raw_password)
        elif raw_password:
            # 3. При редактировании обновляем хеш только если ввели новый пароль.
            model.password_hash = hash_password(raw_password)

        return await super().on_model_change(data, model, is_created, request)
```

### Чек-лист "виртуальное поле в SQLAdmin"

Когда нужно добавить в форму поле, которого нет в SQLAlchemy-модели:

1. [ ] Убрать имя поля из `form_columns` (иначе KeyError в scaffold_form).
2. [ ] Не использовать `form_extra_fields` - в sqladmin его нет.
3. [ ] Переопределить `async def scaffold_form(self)` - через `super()` + `form_class.<name> = ...`.
4. [ ] На форме использовать `validators.Optional()` (если поле нужно только при create - валидация в `on_model_change`).
5. [ ] В `on_model_change` первым делом `data.pop("<name>", None)`.
6. [ ] Вручную положить обработанное значение в модель через `model.<real_column> = ...`.

### Что не работает и почему

| Попытка | Результат |
|---|---|
| `form_columns = [..., "password", ...]` | `KeyError: 'password'` в `mapper.attrs[name]` |
| `form_overrides = {"password": PasswordField}` | Не создает поле, только подменяет тип у существующих |
| `form_extra_fields = {"password": PasswordField(...)}` | Тихо игнорируется в sqladmin 0.17 (это Flask-Admin фича) |
| Оставить `password` в `data` без `pop` | `AttributeError` / молчаливое `setattr` на модель |

### Общий принцип

Любое **виртуальное поле формы** (пароль, "подтвердите пароль", "прикрепить файл, но не в модель", капча, чекбокс подтверждения и т.п.) в SQLAdmin реализуется через связку:

```
scaffold_form()   -> добавить поле в WTForms-класс
on_model_change() -> data.pop() + ручная запись в реальную колонку
```
## Общий урок для SQLAdmin
Никогда не клади Model.column (или Model.relationship ) в атрибут класса ModelView — только имена строкой. Это же ограничение действует и для любых кастомных полей вроде default_sort_column , если делать по-своему. Стандартные атрибуты SQLAdmin ( column_list , column_sortable_list и пр.) как раз поэтому принимают строки

---

## Перехват ошибок SQLAdmin: middleware для показа traceback

**Дата фиксации:** 2026-08-07
**Версия sqladmin:** 0.17.0

### Проблема

При ошибке в admin-маршруте (например `/admin/content-dashboard`) показывается белый экран с `500 Internal Server Error` — без traceback, без типа исключения, без файла и строки.

### Почему стандартные подходы НЕ работают в sqladmin 0.17.0

#### 1. `BaseHTTPMiddleware` не ловит исключения SQLAdmin

`BaseHTTPMiddleware.call_next()` НЕ пробрасывает исключения. Starlette ловит их раньше через свой внутренний `ServerErrorMiddleware` и возвращает generic `500`. Ваш `try/except` вокруг `call_next` никогда не сработает.

#### 2. SQLAdmin НЕ наследует Starlette

```python
# sqladmin 0.17.0
Admin MRO: ['Admin', 'BaseAdminView', 'BaseAdmin', 'object']
```

У `Admin` НЕТ метода `add_middleware()`. Нельзя сделать `admin.add_middleware(MyMiddleware)`.

#### 3. `admin.app` — это FastAPI, а НЕ внутренний Starlette SQLAdmin

```python
admin = Admin(app, engine, ...)  # app — FastAPI
admin.app  # это FastAPI app, переданный в конструктор!
```

`app.add_exception_handler(Exception, handler)` регистрирует handler на FastAPI, но SQLAdmin его НЕ видит.

#### 4. SQLAdmin создаёт СВОЙ внутренний Starlette instance

В sqladmin 0.17.0 в `BaseAdmin.__init__`:
```python
self.admin = Starlette(middleware=middlewares)
```

Все admin-роуты идут через `admin.admin` (внутренний Starlette), а не через FastAPI. Именно на этот внутренний Starlette нужно регистрировать exception handler.

### Правильное решение

Файл: `app/middleware/admin_error_middleware.py`

#### Шаг 1: Получить внутренний Starlette SQLAdmin

```python
inner_starlette = admin_instance.admin  # НЕ admin_instance.app!
```

#### Шаг 2: Зарегистрировать exception handler на внутреннем Starlette

```python
@inner_starlette.exception_handler(Exception)
async def _sqladmin_exception_handler(request, exc):
    # Логируем полный traceback
    logger.exception("SQLAdmin Exception на %s %s: %s", request.method, request.url.path, exc)
    # Возвращаем детальную страницу ошибки
    error_html = _render_error_page(exc, request.method, request.url.path, str(request.query_params), 0)
    return HTMLResponse(content=error_html, status_code=500, headers={"x-admin-error-handled": "true"})
```

#### Шаг 3: Внешний ASGI-middleware как fallback

Для «тихих» 500 (когда exception handler не сработал) — перехватываем через ASGI send wrapper:

```python
class AdminErrorMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith("/admin"):
            await self.app(scope, receive, send)
            return

        status_code = 200
        intercepted = False
        body_chunks = []

        async def send_wrapper(message):
            nonlocal status_code, intercepted
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers = message.get("headers", [])
                # Не перехватываем, если exception handler уже обработал
                already_handled = any(k.decode().lower() == "x-admin-error-handled" for k, _ in headers)
                if status_code >= 500 and not already_handled:
                    intercepted = True
                    return
                await send(message)
            elif message["type"] == "http.response.body":
                if intercepted:
                    body = message.get("body", b"")
                    if body:
                        body_chunks.append(body)
                    if not message.get("more_body", False):
                        await self._render_error(send, scope, body_chunks)
                    return
                await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            # Fallback: если исключение прошло сквозь всё
            ...
```

#### Шаг 4: Установка в main.py

```python
from app.middleware import AdminErrorMiddleware, register_admin_error_handler, install_exception_catcher

# 1. Создаём SQLAdmin
admin = Admin(app, engine, authentication_backend=authentication_backend)

# 2. Устанавливаем exception catcher ВНУТРЬ SQLAdmin
install_exception_catcher(admin)  # Использует admin.admin (внутренний Starlette)

# 3. Регистрируем views
for view in ALL_ADMIN_VIEWS:
    admin.add_view(view)

# 4. Регистрируем exception handler на FastAPI (для не-SQLAdmin маршрутов)
register_admin_error_handler(app)

# 5. Добавляем внешний ASGI middleware (fallback)
app.add_middleware(AdminErrorMiddleware)
```

### Ключевые архитектурные факты о sqladmin 0.17.0

| Что | Значение |
|-----|----------|
| `Admin` наследует | `BaseAdmin` (НЕ `Starlette`) |
| `admin.app` | FastAPI app (переданный в конструктор) |
| `admin.admin` | Внутренний Starlette instance (обрабатывает все admin-роуты) |
| `admin.add_middleware()` | НЕ существует |
| `admin.app.add_middleware()` | Добавляет в FastAPI, НЕ в SQLAdmin |
| `admin.admin.add_middleware()` | Добавляет во внутренний Starlette SQLAdmin ✅ |
| `admin.admin.exception_handler()` | Регистрирует handler на внутреннем Starlette ✅ |
| `app.add_exception_handler()` | Регистрирует на FastAPI, SQLAdmin НЕ видит ❌ |

### Чек-лист: перехват ошибок SQLAdmin

1. [ ] НЕ использовать `BaseHTTPMiddleware` для перехвата исключений (не работает)
2. [ ] НЕ регистрировать exception handler на FastAPI (`app.add_exception_handler`) — SQLAdmin не видит
3. [ ] Использовать `admin.admin` для доступа к внутреннему Starlette SQLAdmin
4. [ ] Регистрировать `@admin.admin.exception_handler(Exception)` для ловли исключений
5. [ ] Добавлять ASGI-middleware на `admin.admin.add_middleware()` для внутреннего перехвата
6. [ ] Использовать внешний ASGI-middleware как fallback для «тихих» 500
7. [ ] Маркировать обработанные ответы заголовком `x-admin-error-handled`
8. [ ] Показывать traceback через `traceback.format_exception(type(exc), exc, exc.__traceback__)`

### Антипаттерны (что НЕ работает)

| Попытка | Результат |
|---------|-----------|
| `BaseHTTPMiddleware` + `try/except call_next` | Не ловит исключения, Starlette перехватывает раньше |
| `app.add_exception_handler(Exception, handler)` | SQLAdmin не видит, использует свой Starlette |
| `admin.add_middleware(...)` | `AttributeError` — у Admin нет этого метода |
| `admin.app.add_middleware(...)` | Добавляет в FastAPI, а не в SQLAdmin |
| `admin.app.exception_handler(...)` | Регистрирует на FastAPI, SQLAdmin не видит |

### Структура файлов

```
app/middleware/
├── __init__.py                    # Экспорт: AdminErrorMiddleware, register_admin_error_handler, install_exception_catcher
└── admin_error_middleware.py       # Вся логика перехвата ошибок
    ├── _render_error_page()       # Детальная страница с подсветкой traceback
    ├── _render_failsafe_page()    # Простой HTML failsafe
    ├── AdminErrorMiddleware       # Внешний ASGI-middleware (fallback)
    ├── _SQLAdminExceptionCatcher  # Внутренний ASGI-middleware (contextvar)
    ├── install_exception_catcher  # Установка на admin.admin
    └── register_admin_error_handler # Exception handler на FastAPI
```
