# Экранирование и доза — учебный веб‑симулятор (Streamlit)

**Назначение.** Визуализирует влияние расстояния и экранов на условную мощность дозы.  
Модель учебная: коэффициенты μ относительные, типы излучений — **гамма, бета, альфа, нейтроны**.

## Возможности
- RU/EN локализация (переключатель в сайдбаре).
- Экспорт графиков в **PNG** и данных кривой **D(r)** в **CSV**.
- Типы излучений с различными μ по материалам; подсказки к выбору материалов.
- Сохранение сценариев с метаданными (**author, note, saved_at, radiation_type**).
- Страницы:
  - **Comparison / Сравнение** — две кривые и метаданные сценариев;
  - **Quiz / Квиз** — RU/EN вопросник (контент учебный);
  - **μ table** — сводная таблица μ с выгрузкой в CSV;
  - **μ editor** — редактирование μ, горячие пресеты (гамма‑жёсткие, нейтрон‑оптимизированные, бета‑безопасные, альфа‑суперпорог), защищённое сохранение и сброс;
  - **scenarios_io** — экспорт/импорт сценариев (JSON/ZIP, стратегии при конфликтах);
  - **export_bundle** — пакетный ZIP (PNG+CSV для выбранных сценариев, сравнение, μ‑таблица, пресет μ);
  - **Стоимость vs Снижение D** — простая «финтех»‑метрика полезности экрана.

> Дисклеймер: проект учебный, без привязки к референсным нормам; значения μ и выводы иллюстративны.

## Требования
- **Python 3.10+** установлен в системе (Windows).
- Интернет не обязателен (работает офлайн после установки зависимостей).

## Установка и запуск на Windows (Python уже установлен)

1. **Распакуйте архив** `kurchatov-shielding-sim.zip` в, например: `C:\Projects\kurchatov-shielding-sim`.

2. **Откройте терминал** в папке проекта (Windows Terminal / PowerShell / cmd):
   ```powershell
   cd C:\Projects\kurchatov-shielding-sim
   ```

3. **Создайте виртуальное окружение и активируйте его**:
   ```powershell
   py -m venv .venv
   # PowerShell:
   .\.venv\Scripts\Activate.ps1
   # если PowerShell жалуется на политику выполнения (ExecutionPolicy):
   # Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   # Либо cmd.exe:
   # .\.venv\Scripts\activate.bat
   ```

4. **Обновите pip и установите зависимости**:
   ```powershell
   python -m pip install -U pip setuptools wheel
   python -m pip install -r requirements.txt
   ```

5. **Запустите приложение**:
   ```powershell
   streamlit run app.py
   # или, если streamlit не найден в PATH:
   python -m streamlit run app.py
   ```
   По умолчанию откроется `http://localhost:8501`. Если порт занят:
   ```powershell
   streamlit run app.py --server.port 8502
   ```

### Быстрая проверка
- В сайдбаре: выберите **Язык / Language**, **Вид излучения**, настройте слои экрана.
- Блок **Сценарии**: заполните *Название, Автор, Заметка* → **Сохранить** (папка `scenarios` создаётся автоматически; к имени добавится суффикс с типом, напр. `[Гамма]`).
- Под графиком доступны кнопки **PNG** и **CSV**.
- Переключите страницы в левом меню (Comparison, Quiz, μ table, μ editor, scenarios_io, export_bundle, Стоимость vs Снижение D).

### Где хранятся данные
- Сценарии: `scenarios/my_scenarios.json`  
- Пользовательский пресет μ: `data/mu_override.json`  
Перед обновлением проекта экспортируйте сценарии (страница **scenarios_io**) и/или сохраните файл пресета.

### Частые проблемы
- **`streamlit: command not found`** — активируйте окружение или используйте `python -m streamlit run app.py`.
- **PNG‑экспорт не работает (kaleido)** — установите/переустановите `kaleido` из `requirements.txt`:
  ```powershell
  python -m pip install -U kaleido
  ```
- **`ModuleNotFoundError: No module named 'sklearn'`** — проверьте, что окружение активно, и выполните:
  ```powershell
  python -m pip install -r requirements.txt
  ```
- **Порт 8501 занят** — запустите на другом порту: `--server.port 8502`.
- **Пути с пробелами/кириллицей** — по возможности используйте простой путь, например `C:\Projects\kurchatov-shielding-sim`.

## Альтернативный запуск (Unix/macOS)
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
streamlit run app.py
```

## Экспорт пакета артефактов
Страница **export_bundle** формирует ZIP с PNG+CSV по выбранным сценариям (и сравнением при выборе 2 сценариев). Можно добавить таблицу μ и текущий `mu_override.json`.

## Лицензия и авторство
Учебное ПО для демонстрационных целей в рамках проектного интенсива. Используйте с пониманием ограничений модели.
