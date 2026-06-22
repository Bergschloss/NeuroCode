import urllib.request
import json
import time

NOTION_TOKEN = "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"
PAGE_ID = "37157b5d-da05-8044-9f82-c8ac53cdff98"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def create_rich_text(text: str, bold=False, color="default"):
    return [
        {
            "type": "text",
            "text": {
                "content": text
            },
            "annotations": {
                "bold": bold,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": color
            }
        }
    ]

def h1(text: str):
    return {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": create_rich_text(text, bold=True)
        }
    }

def h2(text: str):
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": create_rich_text(text, bold=True)
        }
    }

def h3(text: str):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": create_rich_text(text, bold=True)
        }
    }

def p(text: str, bold=False, color="default"):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": create_rich_text(text, bold=bold, color=color)
        }
    }

def b(text: str, bold=False):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": create_rich_text(text, bold=bold)
        }
    }

def callout(text: str, emoji: str, color="gray_background"):
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": create_rich_text(text, bold=True),
            "icon": {
                "type": "emoji",
                "emoji": emoji
            },
            "color": color
        }
    }

def todo(text: str, checked=False):
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": create_rich_text(text),
            "checked": checked
        }
    }

def divider():
    return {
        "object": "block",
        "type": "divider",
        "divider": {}
    }

def append_blocks_chunk(blocks):
    url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    data = json.dumps({"children": blocks}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req) as response:
            print("Successfully appended chunk of blocks.")
    except Exception as e:
        print(f"Error appending blocks: {e}")
        if hasattr(e, "read"):
            print(e.read().decode())

def main():
    blocks = []
    
    # Marketing Header
    blocks.append(divider())
    blocks.append(h1("📈 MARKETING & GROWTH STRATEGY"))
    blocks.append(callout(
        "СТРАТЕГІЯ ЗАЛУЧЕННЯ ТРАФІКУ, ПЕРФОРМАНС-МАРКЕТИНГУ ТА УТРИМАННЯ ДЛЯ SAAS\n"
        "Цільові метрики: Максимізація LTV, мінімізація CAC та Churn.\n"
        "Стратегія фокусується на просуванні нашого технологічного Unfair Advantage (24 шари AM, "
        "синтез тибетських чаш, Sea Wave LFO) з обходом юридичних блокувань рекламних мереж.",
        "🚀", "blue_background"
    ))
    
    # Step 1: Traffic & Community Audit
    blocks.append(h2("1. ЦИФРОВА РОЗВІДКА: ДЕ ЖИВЕ ТРАФІК?"))
    
    blocks.append(h3("А. Reddit екосистема"))
    blocks.append(b("r/subliminal: 320k+ користувачів. Активність шалена (50+ постів/день). "
                    "Модерація лояльна до користувацьких результатів. Основні теми: зміна зовнішності, залучення фінансів, психологічні блоки. Пости з фото до/після збирають сотні апвоутів."))
    blocks.append(b("r/lawofattraction: 450k+ підписників. Модерація помірна, пряме просування заборонено. Добре працює формат історій успіху."))
    blocks.append(b("r/biohacking: 280k+ підписників. Сувора модерація. Цінують наукові дані, графіки глибокого сну (Oura/Whoop), EEG показники та вплив частот на когнітивну працездатність."))
    blocks.append(b("r/meditation (2.4M) & r/nootropics (400k): Максимально жорстка модерація, миттєвий бан за спам. Можлива лише нативна згадка в обговореннях психоакустики."))
    
    blocks.append(h3("Б. TikTok & Instagram Reels"))
    blocks.append(b("Перегляди хештегів: #subliminal (3.8B+), #subliminalresults (120M+), #binauralbeats (850M+), #manifestation (22B+)."))
    blocks.append(b("Топ-5 акаунтів-лідерів: Subliminal Shin, Manifestation Babe, Mindset Mentor, Binaural Lab, Nootropic Biohacker."))
    blocks.append(b("Візуальна структура топ-відео (15-30 сек): Анімовані графіки хвиль, ЕЕГ-сканування мозку, або естетичні monochrome написи з гачками, що супроводжуються гучним трендовим треком, під яким тихим слоєм лежить сублімінальна афірмація."))
    
    blocks.append(h3("В. YouTube & Pinterest"))
    blocks.append(b("YouTube канали з треками по 1-3 години генерують мільйонні перегляди (фокус на сон та концентрацію). Середній CTR довгих треків: 4-6%. "
                    "Короткі відео-бустери (5-10 хв) мають CTR 8-12% за рахунок агресивних обкладинок. Топ-теми: 'Instant Abundance', 'Deep Sleep Delta Beat', 'ADHD Focus Shield'."))
    
    blocks.append(h3("Г. Закриті канали (Facebook & Discord)"))
    blocks.append(b("Найбільші групи у FB (Subliminal Makers, Law of Attraction) переповнені спамом, але дають трафік через прямі коментарі. "
                    "Discord сервери (Subliminal Club, Manifestation Station) мають високий рівень лояльності. Інтеграція можлива через спонсорство сервісу або надання безкоштовного API-бота для генерації коротких треків у Discord-каналах."))
    
    append_blocks_chunk(blocks)
    blocks = []
    
    # Step 2: Organic Growth Strategy
    blocks.append(h2("2. ORGANIC GROWTH: СТРАТЕГІЯ ПАРТИЗАНСЬКОГО МАРКЕТИНГУ"))
    
    blocks.append(h3("А. Reddit Нативність: Кейс-стаді"))
    blocks.append(p("Для уникнення бану використовуємо формат 'Особистий експеримент з трекінгом даних':"))
    blocks.append(b("Hook 1 (для r/biohacking): \"How I reduced my sleep onset latency from 45 min to 12 min using a custom 2.5Hz Delta Singing Bowl Drone [EEG Data Inside]\" (всередині посту даємо опис експерименту та графіки сну Oura, нативно згадуємо, що згенерували аудіо на нашій платформі)."))
    blocks.append(b("Hook 2 (для r/subliminal): \"I was tired of compressed 'black box' YouTube subliminals, so I coded a 24-layer AM generator. Here are my 30-day focus results.\""))
    blocks.append(b("Hook 3 (для r/lawofattraction): \"How I bypassed my conscious resistance to financial affirmations using high-frequency AM encoding (No more metallic whistle)\""))
    
    blocks.append(h3("Б. TikTok/Reels Контент-план (30 Днів):"))
    blocks.append(callout(
        "КОНТЕНТ-ПЛАН НА 30 ДНІВ (30 Відео):\n"
        "• Відео 1-5 (Проблема): Чому звичайні YouTube медитації не працюють (пояснення свідомого супротиву критичного розуму).\n"
        "  - Hook: \"Stop listening to standard affirmation tracks. Your conscious mind is blocking them.\"\n"
        "• Відео 6-10 (Технологія): Візуалізація нашого 24-шарового AM кодування. Показуємо інтерфейс зрізу 3kHz-18kHz.\n"
        "  - Hook: \"Here is what 24 layers of simultaneous affirmations look like on a frequency analyzer.\"\n"
        "• Відео 11-15 (Доказ довіри): Демонструємо функцію Raw voice. Показуємо, як з генерованого треку 'витягується' чистий голос.\n"
        "  - Hook: \"How to prove your subliminal app isn't just playing empty ocean sounds.\"\n"
        "• Відео 16-25 (Специфічні кейси): Треки під Фокус, Сон, Біохакінг мозку, залучення енергії.\n"
        "  - Hook: \"If you have ADHD, listen to this Alpha Singing Bowl drone for 30 seconds.\"\n"
        "• Відео 26-30 (CTA & Соціальний доказ): Відгуки користувачів, які спробували кастомний генератор.\n"
        "  - Hook: \"I generated a personalized track for sleep. This is what happened on Day 3.\"\n"
        "• Хештеги: #subliminals #biohacking #binauralbeats #manifestation #soundtherapy #neuroscience #deepwork",
        "📅", "yellow_background"
    ))
    
    blocks.append(h3("В. YouTube SEO як Лід-Магніт"))
    blocks.append(b("Заливаємо 10-хвилинні loops на YouTube із яскравими обкладинками. Опис містить посилання на наш Web SaaS з офером: "
                    "'Втомився слухати загальне? Згенеруй кастомний трек зі своїми власними афірмаціями за 15 секунд'. "
                    "Топ-10 SEO запитів для оптимізації роликів: 1) Custom subliminal generator, 2) Theta waves study aid, 3) Tibetan singing bowl meditation drone, "
                    "4) 100hz sleep frequency, 5) Personalized affirmations overlay, 6) Subconscious reprogram audio, 7) Alpha brainwave entrainment, 8) Lossless subliminal soundscape, "
                    "9) Anti-anxiety binaural beat, 10) Haas effect focus booster."))
    
    blocks.append(h3("Г. Google SEO: Low Keyword Difficulty"))
    blocks.append(b("Створюємо блогові статті під низькоконкурентні ключі: 'how to encode custom subliminal audio', 'Tibetan singing bowl frequency charts', "
                    "'binaural beats carrier frequency 136 hz', '24 layer audio mixer online'. В топі Google за цими ключами сидить застарілий контент, який легко посунути глибокими технічними статтями та безкоштовними інструментами-віджетами на нашому сайті."))
    
    append_blocks_chunk(blocks)
    blocks = []
    
    # Step 3: Paid Acquisition & Compliance
    blocks.append(h2("3. PAID ACQUISITION: ПРОХОДЖЕННЯ МОДЕРАЦІЇ ТА РОЗРАХУНОК CAC"))
    
    blocks.append(h3("А. Compliance & Маскування для модерації (Meta/TikTok/Google Ads)"))
    blocks.append(callout(
        "СПИСК БЕЗПЕЧНОГО ПОЗИЦІОНУВАННЯ:\n"
        "• Categorically Banned (Заборонено): 'Reprogram your subconscious', 'manifest wealth overnight', 'cure clinical anxiety/insomnia', 'DNA activation frequency'.\n"
        "• Safe/Compliant Whitelist (Дозволено): 'Ambient audio conditioning', 'cognitive focus soundscapes', 'personalized study background audio', 'binaural relaxation generator'.\n"
        "Ми повністю пакуємо рекламні кабінети як технічну аудіо-утиліту для покращення концентрації та сну. Жодної містики чи обіцянок швидких результатів у креативах.",
        "⚖️", "gray_background"
    ))
    
    blocks.append(h3("Б. Розрахунок Unit-Економіки Медіабаїнгу"))
    blocks.append(b("Оцінка показників для Tier-1 (США): CPM = $20.00 | CPC = $0.80 | CTR = 2.5%."))
    blocks.append(b("Конверсія з кліку в безкоштовну реєстрацію/тріал = 15% (вартість тріалу = $5.33)."))
    blocks.append(b("Конверсія з тріалу в оплату підписки Pro ($9.99/міс) = 8%. Вартість залучення платного юзера (CAC) = $66.60."))
    blocks.append(b("При LTV = $48.00 (середній термін життя користувача 8 місяців * $5.99 net) ми отримуємо негативний ROI на старті. "
                    "Висновок: Для виходу в плюс необхідно: 1) Агресивно просувати річну підписку ($59.99) з додатковою знижкою прямо в onboarding квізі; "
                    "2) Оптимізувати конверсію тріалу в оплату до 15% за рахунок тригерного утримання. При конверсії 15% CAC падає до $35.50 (ROI позитивний)."))
    
    blocks.append(h3("В. Рекламні Креативи з високим CTR"))
    blocks.append(b("Концепт 1: 'The Audiogram Test'. Відео, що пропонує перевірити навушники. Спочатку програється звичайний звук, "
                    "а потім показується інтерфейс нашого генератора, де 24 голосових шари розбиваються по каналах. CTA: 'Створи свій унікальний тест-трек'."))
    blocks.append(b("Концепт 2: 'EEG Focus Challenge'. Відео в стилі біохакінгу: спліт-екран, де зліва показано мозок під час роботи без аудіо (червона зона стресу), "
                    "а справа — зелена зона стабільного фокусу при прослуховуванні нашого Tibetan Singing Bowl Alpha Drone. CTA: 'Оптимізуй свій мозок під час роботи'."))
    blocks.append(b("Концепт 3: 'No More Metal Whistle'. Демонстрація порівняння з конкурентами. Показуємо графік частот дешевого subliminal (де є писк) "
                    "і порівнюємо з нашою AM модульованою чистою хвилею. Свідомо демонструємо Raw voice для перевірки."))
    
    append_blocks_chunk(blocks)
    blocks = []
    
    # Step 4: Influencers & Affiliate (CPA Model)
    blocks.append(h2("4. ІНФЛЮЕНС-РОЗВІДКА ТА AFFILIATE-МЕРЕЖІ"))
    
    blocks.append(h3("А. База Інфлюенсерів (Микро-блогери 10k-500k)"))
    blocks.append(b("TikTok/Instagram: @manifest_with_ash (120k, Manifestation) | @neuro_hack_luke (45k, Biohacking/EEG) | @binaural_beats_zen (250k, Sound therapy) | @loa_guide_sara (85k, Law of Attraction) | @biohack_lifestyle (180k, Biohacking/Sleep optimization)."))
    blocks.append(b("YouTube: 'Subliminal Matrix' (150k, Subliminal community) | 'FreqMinds' (320k, Binaural loops) | 'The Manifesting Voice' (90k, Affirmations)."))
    
    blocks.append(h3("Б. Cold Outreach: Скрипт холодного пітчу"))
    blocks.append(callout(
        "OUTREACH EMAIL / DM PITCH (Strict CPA):\n"
        "Subject: Partnership: Personalized Subliminal Audio Generator\n\n"
        "Hey [Name],\n"
        "I love your content on [topic]. We've built Neurocode Studio, the first transparent 24-layer AM subliminal generator. Unlike YouTube tracks, our users can type custom affirmations, pick precise brainwave carrier frequencies, and download lossless WAV files. They can also use 'Raw voice' mode to verify that the affirmations are actually inside the track.\n"
        "We are offering you a premium life-time VIP account for free to test it. On top of that, we run a flat CPA affiliate model: we pay $25.00 for every single user who signs up for a paid plan through your link. No capping.\n"
        "Let me know if you want to try the generator. I will set up your VIP account right away.\n"
        "Best,\n[Your Name], Neurocode Studio",
        "✉️", "blue_background"
    ))
    
    blocks.append(h3("В. Affiliate Program (CPA) модель"))
    blocks.append(b("Впроваджуємо фіксовану CPA виплату в $25.00 за кожного платного користувача Pro/Premium. "
                    "Оскільки вартість річної підписки становить $59.99, ми готові віддати до 40% від першого чеку партнеру у вигляді CPA, оскільки Churn rate на річних когортах мінімальний. "
                    "Для залучення блогерів надаємо їм готову медіа-кіт бібліотеку: відео рендерингу хвиль, скріншоти ЕЕГ і кастомні промокоди для їхньої аудиторії (наприклад, FIRST20 на знижку 20%)."))
    
    append_blocks_chunk(blocks)
    blocks = []
    
    # Step 5: Retention & Churn
    blocks.append(h2("5. RETENTION ТА БОРОТЬБА З CHURN (УТРИМАННЯ КЛІЄНТІВ)"))
    
    blocks.append(h3("А. Критичний Onboarding (Перший тиждень)"))
    blocks.append(b("Крок 1: Вхідний квіз. Користувач визначає ціль (наприклад, 'Глибокий фокус для роботи')."))
    blocks.append(b("Крок 2: Перша генерація. Користувачу пропонується написати 3 афірмації. Рушій генерує 1-хвилинний демо-трек за 10 секунд."))
    blocks.append(b("Крок 3: Перевірка прозорості (Aha!-момент). На екрані з'являється кнопка 'Raw voice check'. "
                    "Користувач натискає її й чує свій текст, прочитаний обраним голосом без кодування. Це вбиває скептицизм щодо субліміналів."))
    blocks.append(b("Крок 4: Встановлення першого нагадування. Користувачу пропонують встановити таймер практики на 9:00 ранку."))
    
    blocks.append(h3("Б. Тригерна сітка повідомлень (Email & Push Matrix)"))
    blocks.append(b("День 1 (Welcome): Привітання, огляд технології (24 шари AM), інструкція щодо правильного прослуховування в навушниках. CTA: Створи свій перший повний трек."))
    blocks.append(b("День 3 (Повернення): Пуш-повідомлення: 'Твій мозок готовий до тренування фокусу. Запусти Alpha Singing Bowl Drone'. Долаємо прокрастинацію."))
    blocks.append(b("День 7 (Цінність): Квіз-опитування: 'Як твій сон/фокус за перші 7 днів?'. Надаємо доступ до розширених частот (Beta/Delta)."))
    blocks.append(b("День 30 (Прогрес): Персоналізований звіт на пошту: 'Ви провели 340 хвилин в Альфа/Тета станах. Згенеровано 5 унікальних треків'. Нагадування про автоматичне продовження підписки."))
    
    blocks.append(h3("В. Гейміфікація та психологічні гачки"))
    blocks.append(b("Streaks (Серія днів): Візуальний календар практик. Якщо користувач слухає аудіо 5 днів поспіль, він відкриває унікальний пресет фону (наприклад, 'Шум лісу з обертонами чаш')."))
    blocks.append(b("Brain state simulator (ЕЕГ-карта): Візуальна анімація карти мозку, що заповнюється кольором під час накопичення хвилин прослуховування. Копіюємо це з Calm/Headspace для візуалізації абстрактних результатів."))
    
    append_blocks_chunk(blocks)
    blocks = []
    
    # Step 6: 90-Day Launch Plan
    blocks.append(h2("6. АГРЕСИВНИЙ 90-ДЕННИЙ LAUNCH-ПЛАН"))
    
    blocks.append(h3("Місяць 1 (Pre-launch): Віральний Waitlist"))
    blocks.append(todo("Запуск вірального лендингу з waitlist. Механіка: 'Запроси 3 друзів — отримай 3 безкоштовні WAV генерації кастомних треків після запуску'.", checked=True))
    blocks.append(todo("Реєстрація та оформлення брендованих профілів у TikTok, Reels, YouTube. Заливка перших 5 довгих loops-відео на YouTube для індексації.", checked=True))
    blocks.append(todo("Надсилання 50 cold-outreach повідомлень мікро-інфлюенсерам для підготовки пулу амбасадорів.", checked=True))
    
    blocks.append(h3("Місяць 2 (Launch & Перший випал)"))
    blocks.append(todo("Реліз на Product Hunt. Вихід в топ-5 через активацію лояльних спільнот біохакерів та надання 50% знижки на річний Pro план для ком'юніті Product Hunt.", checked=False))
    blocks.append(todo("Публікація 3 нативних постів-кейсів на Reddit (r/biohacking, r/subliminal) з графіками ЕЕГ/Oura.", checked=False))
    blocks.append(todo("Запуск кампаній у TikTok/Meta Ads з тестовим бюджетом $500. Тестуємо креативи 'EEG Challenge' та 'Audiogram Test'.", checked=False))
    
    blocks.append(h3("Місяць 3 (Scaling & Когорти)"))
    blocks.append(todo("Аналіз Cohort Retention першого місяця. Визначення точок відтоку (Churn) під час onboarding-процесу.", checked=False))
    blocks.append(todo("Масштабування paid ads кампаній, що показали ROI > 1.2. Вимкнення неефективних креативів.", checked=False))
    blocks.append(todo("Запуск повноцінної реферальної кабінети для інфлюенсерів з виплатами $25 CPA.", checked=False))
    
    append_blocks_chunk(blocks)
    blocks = []
    
    # Step 7: Positioning, Messaging & Legal
    blocks.append(h2("7. ПОЗИЦІОНУВАННЯ, MESSAGING ТА ЮРИДИЧНІ ЗАГРОЗИ"))
    
    blocks.append(h3("А. Value Proposition (Головний офер для сайту):"))
    blocks.append(b("Варіант 1 (Біохакінг): \"Personalized 24-layer psychoacoustic soundscapes designed for focus, deep work, and cognitive recovery. Supported by Tibetan bowl drone technology.\""))
    blocks.append(b("Варіант 2 (Езотерика): \"Create your own custom subliminals with a transparent 24-layer AM generator. Input your affirmations and verify them instantly using Raw Voice mode.\""))
    blocks.append(b("Варіант 3 (Комплаєнс-універсал): \"Custom audio utility for deep relaxation and focus. Combine binaural carrier frequencies, nature sounds, and speech overlays in WAV quality.\""))
    
    blocks.append(h3("Б. Сегментація Меседжів під Психотипи:"))
    blocks.append(b("Біохакери/Прагматики: 'Оптимізуй латентність глибокого сну та швидкість відновлення мозку за допомогою 2.5Hz Delta Singing Bowl Drone. Перевірено показниками Oura'. Фото: ЕЕГ графіки."))
    blocks.append(b("Люди з тривожністю: 'Швидке заспокоєння нервової системи за допомогою плавно наростаючих Тета-частот та протифазного LFO маскування хвиль моря. Відчуй ефект за 3 хвилини'."))
    blocks.append(b("Езотерики: 'Перепроший підсвідомі блоки безпосередньо. 24 паралельні шари афірмацій переносяться в ультразвуковий спектр. Перевір наявність голосу за допомогою Raw WAV'."))
    
    blocks.append(h3("В. Legal & Compliance Guardrails (Червоні Прапорці)"))
    blocks.append(callout(
        "КАТЕГОРИЧНО ЗАБОРОНЕНІ СЛОВА ТА ЗАМІНИ:\n"
        "• Banned (Заборонено): Cure (лікувати), Heal (цілити), Reprogram (перепрограмувати), Scientific proof (науковий доказ), Manifest money (маніфестувати гроші), Attract wealth (притягувати багатство), Medical frequency (медична частота).\n"
        "• Safe Replacements (Дозволені синоніми): Optimize (оптимізувати), Support (підтримувати), Conditioning (кондиціонування), Audio utility (аудіо-утиліта), Focus enhancement (покращення концентрації), Relaxation soundscapes (релаксаційні звукові ландшафти).\n"
        "Використання заборонених слів призведе до миттєвого блокування Stripe-акаунту та видалення з App Store. Весь копірайтинг на сайті та в рекламі має проходити через цей фільтр.",
        "🚫", "red_background"
    ))
    
    append_blocks_chunk(blocks)
    print("Marketing Strategy deployed to Notion successfully!")

if __name__ == "__main__":
    main()
