"""Тести класифікатора мови ніші lake.is_ru / recompute_ru (28.11: прапорець ru пропускав KurilinLab, JustUser, «Абузим сервисы»).
python3 -m pytest -q studio/tests/test_lake_ru.py
"""
import sqlite3, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "yt"))
import lake  # noqa: E402


class IsRu(unittest.TestCase):
    def test_russian_without_special_letters(self):
        self.assertTrue(lake.is_ru("Gemini 4 Hydrogen бесплатно: где взять новую модель Google", "Абузим сервисы | ИИ беспл"))
        self.assertTrue(lake.is_ru("Клод ревнует. Кодекс удаляет. #нейросети #вайбкодинг"))

    def test_ukrainian_and_english(self):
        self.assertFalse(lake.is_ru("ChatGPT, Intel занесли? Покращив фото AMD Ryzen — вийшов Core i7!"))
        self.assertFalse(lake.is_ru("Як вимкнути навчання ChatGPT на твоїх чатах"))
        self.assertFalse(lake.is_ru("Claude Code tutorial for beginners"))
        self.assertFalse(lake.is_ru("Новий Claude"))          # нейтральна кирилиця — не рос.

    def test_frequency_wins(self):
        self.assertTrue(lake.is_ru("Всё это ещё и бесплатно", "Перевір"))        # рос. ознак більше
        self.assertFalse(lake.is_ru("Привіт, це шоу «ШІкарно» про ШІ", "ещё"))   # укр. більше

    def test_lang_of(self):
        self.assertEqual(lake.lang_of("KurilinLab", "Шкаф ниже потолка: кухню рассчитал Claude", "Нейросеть сделала ремонт"), "ru")
        self.assertEqual(lake.lang_of("Шкаф ниже потолка"), "cyr")   # один заголовок без ознак — невизначено (тому рахуємо по каналу)
        self.assertEqual(lake.lang_of("ШІкарно", "новини ШІ українською"), "uk")
        self.assertEqual(lake.lang_of("AI news"), "en")


class Recompute(unittest.TestCase):
    def setUp(self):
        self.c = sqlite3.connect(":memory:")
        self.c.executescript("""
        create table niche(video_id text, fetched text, channel text, title text, published text, duration_s int, views int, channel_subs int, ratio real, ru int, primary key(video_id,fetched));
        create table comp(channel_id text, date text, title text, subs int, views int, videos int, country text, lang text, primary key(channel_id,date));
        create table comp_videos(video_id text primary key, channel_id text, title text, published text, duration_s int, views int, likes int, comments int, fetched text);""")
        ins = lambda vid, ch, t: self.c.execute("insert into niche values(?,?,?,?,?,?,?,?,?,0)", (vid, "2026-11-28", ch, t, "2026-11-27", 30, 1000, 10, 10.0))
        ins("a", "KurilinLab", "Шкаф ниже потолка, а встать не сможет: кухню по картинке рассчитал Claude Opus 5.5")
        ins("b", "JustUser", "Когда ИИ разнёс собственный код #claudecode")
        ins("c", "JustUser", "Два пикселя, Клод #claudecode")
        ins("d", "ШІ для тебе", "Як ШІ допоможе тобі з роботою")
        ins("e", "Абузим сервисы | ИИ беспл", "Gemini 4 Hydrogen бесплатно: где взять новую модель Google")
        self.c.execute("insert into comp values('UC1','2026-11-23','KurilinLab',1,1,1,'','cyr')")
        self.c.execute("insert into comp_videos values('v1','UC1','Нейросеть сделала ремонт','2026-11-20',30,1,1,1,'2026-11-23')")
        self.c.execute("insert into comp values('UC2','2026-11-23','Майстер ремонту',1,1,1,'','ru')")   # старе «ru» з опису
        self.c.execute("insert into comp_videos values('v2','UC2','Код 43 на відеокарті: ігри не запускаються','2026-11-20',30,1,1,1,'2026-11-23')")

    def test_channel_level_flag(self):
        n = lake.recompute_ru(self.c)
        ru = dict(self.c.execute("select channel, max(ru) from niche group by channel").fetchall())
        self.assertEqual(ru, {"KurilinLab": 1, "JustUser": 1, "Абузим сервисы | ИИ беспл": 1, "ШІ для тебе": 0})
        self.assertEqual(self.c.execute("select count(*) from niche where channel='JustUser' and ru=1").fetchone()[0], 2)
        self.assertEqual(dict(self.c.execute("select title, lang from comp").fetchall()), {"KurilinLab": "ru", "Майстер ремонту": "uk"})
        self.assertEqual((n["niche_to_ru"], n["comp_to_ru"], n["comp_from_ru"]), (3, 1, 1))
        self.assertEqual(lake.recompute_ru(self.c)["niche_to_ru"], 0)   # ідемпотентно


if __name__ == "__main__":
    unittest.main()
