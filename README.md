# Экранирование и доза — учебный веб-симулятор (Streamlit)

Назначение: показать, как расстояние и экраны влияют на относительную мощность дозы. Модель учебная.

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate   # Win: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Страницы
- Главная: симулятор, ассистент, экспорт PNG.
- pages/compare.py: сравнение 2 сценариев + экспорт PNG.
- pages/quiz.py: квиз.
- pages/finance.py: стоимость vs снижение D.
