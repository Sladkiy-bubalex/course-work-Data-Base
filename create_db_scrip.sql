CREATE TABLE IF NOT EXISTS Default_words (
	id SERIAL PRIMARY KEY,
	original_word VARCHAR(60) NOT NULL,
	translate_word  VARCHAR(60) NOT NULL,
	option1 VARCHAR(60) NOT NULL,
	option2 VARCHAR(60) NOT NULL,
	option3 VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS Users (
	id SERIAL PRIMARY KEY,
	tg_user_chat_id INT UNIQUE NOT NULL,
	step_user INT
);
	
CREATE TABLE IF NOT EXISTS New_user_word (
	id SERIAL PRIMARY KEY,
	original_word VARCHAR(60) NOT NULL,
	translate_word VARCHAR(60) NOT NULL,
	option1 VARCHAR(60) NOT NULL,
	option2 VARCHAR(60) NOT NULL,
	option3 VARCHAR(60) NOT NULL,
	user_id INT REFERENCES Users(tg_user_chat_id) ON DELETE CASCADE,
	UNIQUE (original_word)
);

CREATE TABLE IF NOT EXISTS Delete_user_word (
	id SERIAL PRIMARY KEY,
	russian_word VARCHAR(60) NOT NULL,
	user_id INT REFERENCES Users(tg_user_chat_id) ON DELETE CASCADE,
	UNIQUE (russian_word)
);

INSERT INTO Default_words (original_word, translate_word, option1, option2, option3)
	 VALUES ('Работа', 'Work', 'Eat', 'Sleep', 'Running'),
	 		('Учиться', 'Study', 'Play', 'Jump', 'Go'),
	 		('Яблоко', 'Apple', 'Banana', 'Peach', 'Wheel'),
	 		('Компьютер', 'Computer', 'Keyboard', 'Mouse', 'Helicopter'),
	 		('Кружка', 'Mug', 'Monitor', 'Bus', 'Noise'),
	 		('Романтика', 'Romance', 'Romantic', 'Romanticize', 'Cheese'),
	 		('Логистика', 'Logictics', 'Physics', 'Chemistry', 'Literature'),
	 		('Ночь', 'Night', 'Midnight', 'Twilight', 'Darkness'),
	 		('Дерево', 'Tree', 'Bush', 'Grass', 'Console'),
	 		('Автобус', 'Bus', 'Catamaran', 'Row', 'Castle');