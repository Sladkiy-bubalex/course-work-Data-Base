import psycopg2
import os


os.environ["name_db"] = input("Название базы данных: ")
os.environ["name_user_db"] = input("Имя пользователя базы данных: ")
os.environ["password_db"] = input("Пароль от базы данных: ")


def words(chat_id: int, auto_id: int) -> tuple:
    """
    Получение всех слов, путем создания 2-ух временных таблиц
    Получение набора слов по id.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем
    auto_id: int\n
        Id набора слов в результирующей таблице (шаг пользователя)

    Возвращает
    -----------
    Кортеж слов (русское слово, англ. перевод, вариант 1, вариант 2, вариант 3)
    """

    with psycopg2.connect(
        database=os.environ["name_db"],
        user=os.environ["name_user_db"],
        password=os.environ["password_db"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """WITH combined AS (
	                   SELECT original_word, translate_word, option1, option2, option3 FROM default_words
	                UNION ALL
	                   SELECT original_word, translate_word, option1, option2, option3 FROM new_user_word
                        WHERE user_id = %s
                    ),
                    numbered AS (
                        SELECT ROW_NUMBER () OVER() AS auto_id, original_word, translate_word, option1, option2, option3 FROM combined
                        WHERE original_word NOT IN (SELECT russian_word FROM delete_user_word WHERE user_id = %s)
                    )
                    SELECT * FROM numbered
                    WHERE auto_id = %s""",
                (chat_id, chat_id, auto_id),
            )
            return cur.fetchone()
    conn.close()


def new_user_for_db(chat_id: int) -> None:
    """
    Передает id чата в БД.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем
    """

    with psycopg2.connect(
        database=os.environ["name_db"],
        user=os.environ["name_user_db"],
        password=os.environ["password_db"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO Users(tg_user_chat_id, step_user)
                        VALUES (%s, %s);""",
                (chat_id, 1),
            )
    conn.close()


def update_step_user_db(chat_id: int, step: int) -> None:
    """
    Обновляет шаг пользователя в БД.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем
    step: int\n
        Шаг пользователя
    """

    with psycopg2.connect(
        database=os.environ["name_db"],
        user=os.environ["name_user_db"],
        password=os.environ["password_db"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE Users
                            SET step_user = %s
                            WHERE tg_user_chat_id = %s;""",
                (step, chat_id),
            )
    conn.close()


def select_step_user_db(chat_id: int) -> tuple:
    """
    Получение из БД шага пользователя.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    Кортеж с номером шага
    """
    with psycopg2.connect(
        database=os.environ["name_db"],
        user=os.environ["name_user_db"],
        password=os.environ["password_db"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT step_user FROM Users
                            WHERE tg_user_chat_id = %s;""",
                (chat_id,),
            )
            return cur.fetchone()
    conn.close()


def add_word_user(text: str, chat_id: int):
    """
    Добавление слова пользователем.

    Параметры
    -----------
    text: str\n
        список слов (русское слово, англ. перевод, вариант 1, вариант 2, вариант 3)
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    При удачном добавлении: количество проходимых слов у пользователя\n
    При повторной попытке добавить уже добавленное слово: сообщение о том, что слова было добавлено\n
    При не правильном вводе слов: возвращает None
    """

    with psycopg2.connect(
        database=os.environ["name_db"],
        user=os.environ["name_user_db"],
        password=os.environ["password_db"],
    ) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """INSERT INTO New_user_word(
                                original_word,
                                translate_word,
                                option1, option2,
                                option3,
                                user_id
                        )
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;""",
                    (
                        text[0].strip(),
                        text[1].strip(),
                        text[2].strip(),
                        text[3].strip(),
                        text[4].strip(),
                        chat_id,
                    ),
                )
            except (
                psycopg2.errors.ForeignKeyViolation,
                psycopg2.errors.UniqueViolation,
            ):
                return "Данное слово уже было добавлено"
            except IndexError:
                return None
            answer = cur.fetchone()
            if type(answer) == tuple:
                cur.execute(
                    """WITH combined AS (
	                   SELECT original_word, translate_word, option1, option2, option3 FROM default_words
	                UNION ALL
	                   SELECT original_word, translate_word, option1, option2, option3 FROM new_user_word
                        WHERE user_id = %s
                    ),
                    numbered AS (
                        SELECT ROW_NUMBER () OVER() AS auto_id, original_word, translate_word, option1, option2, option3 FROM combined
                        WHERE original_word NOT IN (SELECT russian_word FROM delete_user_word WHERE user_id = %s)
                    )
                    SELECT COUNT(*) FROM numbered;""",
                    (chat_id, chat_id),
                )
                return cur.fetchone()
    conn.close()


def delete_word_user(word: str, chat_id: int):
    """
    Удаляет слово пользователя.

    Параметры
    -----------
    word: str\n
        Русское слово, которе необходимо удалить
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    При удачном выполнении: id добавленного слова\n
    При попытке удалить ранее удаленное слово: сообщение об этом\n
    При вводе отсуствующего слова в изучении: сообщение об этом
    """

    with psycopg2.connect(
        database=os.environ["name_db"],
        user=os.environ["name_user_db"],
        password=os.environ["password_db"],
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                        WITH combined AS (
                               SELECT original_word, translate_word, option1, option2, option3 FROM default_words
                            UNION ALL
                               SELECT original_word, translate_word, option1, option2, option3 FROM new_user_word
                                WHERE user_id = %s
                        )
                        SELECT original_word FROM combined
                        WHERE original_word = %s;""",
                (chat_id, word),
            )
            result = cur.fetchone()
            if word in result:
                try:
                    cur.execute(
                        """INSERT INTO Delete_user_word(russian_word, user_id)
                                VALUES (%s, %s) RETURNING id;""",
                        (word, chat_id),
                    )
                except psycopg2.errors.ForeignKeyViolation:
                    return "Данное слово уже было удалено"
                return cur.fetchone()
            else:
                return "Данного слова нет в изучаемых вами слов"
    conn.close()
