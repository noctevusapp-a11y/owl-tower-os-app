# Addition to the bid-estimating skill (apply in the claude.ai skill editor if the synced copy is not updated)


### Owl Tower cost table (Claude Estimator Construction) — обязательный reference layer

Перед тем как ставить unit price по памяти или "по рынку", открой `references/claude-estimator-construction.md`
(полная таблица: репозиторий `owl-tower-os-app`, `cost-db/data/books/rsmeans_bcc_2022/book_lines_la_latest.xlsx`).
Это машинно считанная копия справочного экземпляра книги 2022 года (national bare costs) с пересчётом
каждой строки в **Los Angeles, последний месяц BLS** (компонент × City Cost Index LA × индекс BLS по компоненту).

Правило применения:
1. Найди строку по `cost_code` (`OT-<section>-<line>`) или по описанию; проверь единицу измерения.
2. `status = verified` — можно использовать как reference (каждое число подтверждено всеми тремя чтениями или арифметикой
   книги, колонки сверены). `machine_read` и `flagged` — не verified: сначала открой страницу книги (`book_page`) и прочитай
   строку сам; не используй их «с допуском» — погрешности к числам не приписываются. `percent_add` — это надбавка в %, не цена.
3. Для текущего бюджета бери колонки `*_la_latest`; для "что говорит книга" — `*_2022`.
4. Замени тем, что лучше: котировка поставщика → material; свои бригады и выработка (`labor_hours` × loaded rate) → labor;
   аренда → equipment. Таблица — ориентир, не котировка; сверху добавляй tax, delivery, GCs, contingency, OH&P компании.
5. Никогда не применяй второй региональный или временной коэффициент: он уже внутри `*_la_latest`.
