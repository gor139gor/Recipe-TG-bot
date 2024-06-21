import telebot
from telebot import types
from db_connect import connect_to_database, close_database_connection
from service.db_service import DbService
from mysqlbase import Session
from models.models import Recipe, Ingredient, Category, Rating, Review

connection = connect_to_database()

TOKEN = 'Your_TG_Bot_Token'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['add_recipe'])
def add_recipe(message):
    try:
        # Отримання списку категорій з бази даних
        session = Session()
        db_service = DbService(session)
        categories = db_service.get_all_categories()

        markup = types.InlineKeyboardMarkup()
        for category in categories:
            button = types.InlineKeyboardButton(text=category.name, callback_data=f"category:{category.name}")
            markup.add(button)

        # Надсилання повідомлення про вибір категорії
        chat_id = message.chat.id
        bot.send_message(chat_id, "Оберіть категорію для рецепту:", reply_markup=markup)

    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('category:'))
def handle_category_selection(call):
    try:
        category_name = call.data.split(':')[1]
        msg = bot.send_message(call.message.chat.id, f"Ви обрали '{category_name}'. Введіть назву рецепту:")
        bot.register_next_step_handler(msg, process_recipe_name, category_name)
    except Exception as e:
        bot.reply_to(call.message, f"Помилка: {str(e)}")


def process_recipe_name(message, category_name):
    try:
        recipe_name = message.text
        # Збереження назви рецепту та перехід до наступного кроку
        msg = bot.send_message(message.chat.id, "Введіть час приготування (у хвилинах):")
        bot.register_next_step_handler(msg, process_cooking_time, category_name, recipe_name)
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def process_cooking_time(message, category_name, recipe_name):
    try:
        cooking_time = int(message.text)
        # Збереження часу приготування та перехід до наступного кроку
        msg = bot.send_message(message.chat.id, "Введіть URL рецепту (якщо немає, введіть -):")
        bot.register_next_step_handler(msg, process_recipe_url, category_name, recipe_name, cooking_time)
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def process_recipe_url(message, category_name, recipe_name, cooking_time):
    try:
        recipe_url = message.text
        # Збереження URL рецепту та перехід до наступного кроку
        msg = bot.send_message(message.chat.id, "Введіть URL зображення рецепту (якщо немає, введіть -):")
        bot.register_next_step_handler(msg, process_recipe_image, category_name, recipe_name, cooking_time, recipe_url)
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def process_recipe_image(message, category_name, recipe_name, cooking_time, recipe_url):
    try:
        image = message.text
        # Збереження URL зображення рецепту та перехід до наступного кроку (введення інгредієнтів)
        msg = bot.send_message(message.chat.id,
                               "Введіть інгредієнти рецепту, розділені комами або пробілами та символами нового рядка. Коли закінчите, натисніть /done:")
        bot.register_next_step_handler(msg, process_recipe_ingredients, category_name, recipe_name, cooking_time,
                                       recipe_url, image, [])
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def process_recipe_ingredients(message, category_name, recipe_name, cooking_time, recipe_url, image,
                               ingredients):
    try:
        ingredient = message.text.strip()  # Отримуємо інгредієнт, введений користувачем
        if ingredient.lower() == "/done":
            # Якщо користувач завершив введення інгредієнтів, переходимо до обробки опису рецепту
            process_recipe_ingredients_done(message, category_name, recipe_name, cooking_time, recipe_url, image,
                                            ingredients)
            return
        else:
            # Додаємо інгредієнт до списку
            ingredients.append(ingredient)
            # Продовжуємо запитувати інгредієнти, поки користувач не завершить введення командою /done
            msg = bot.send_message(message.chat.id,
                                   "Введіть наступний інгредієнт або натисніть /done, щоб завершити:")
            bot.register_next_step_handler(msg, process_recipe_ingredients, category_name, recipe_name, cooking_time,
                                           recipe_url, image, ingredients)
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def process_recipe_ingredients_done(message, category_name, recipe_name, cooking_time, recipe_url, image,
                                    ingredients):
    try:
        # Запит на введення опису
        msg = bot.send_message(message.chat.id, "Введіть опис рецепту:")
        bot.register_next_step_handler(msg, process_recipe_description, category_name, recipe_name, cooking_time,
                                       recipe_url, image,
                                       ingredients)
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def process_recipe_description(message, category_name, recipe_name, cooking_time, recipe_url, image,
                               ingredients):
    try:
        description = message.text
        # Збереження рецепту в базу даних разом з описом та інгредієнтами
        add_recipe_to_database(category_name, recipe_name, cooking_time, recipe_url, image,
                               ingredients, description)
        bot.send_message(message.chat.id, f"Рецепт '{recipe_name}' додано успішно!")
    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


def add_recipe_to_database(category_name, recipe_name, cooking_time, recipe_url, image, ingredients, description):
    try:
        session = Session()
        db_service = DbService(session)

        # Створення нового об'єкта рецепту
        new_recipe = Recipe(name=recipe_name, cooking_time=cooking_time, url=recipe_url, image=image,
                            description=description)

        category = db_service.get_category_by_name(category_name)

        if category:
            new_recipe.categories.append(category)
        else:
            raise ValueError("Такої категорії не існує.")

        # Додавання інгредієнтів до рецепту
        for ingredient_name in ingredients:
            ingredient = Ingredient(name=ingredient_name)
            new_recipe.ingredients.append(ingredient)

        # Збереження нового рецепту в базі даних
        db_service.save_recipes([new_recipe])

    except Exception as e:
        raise e


@bot.message_handler(commands=['search_recipe'])
def handle_search_recipe(message):
    bot.send_message(message.chat.id, "Введіть назву рецепту, який ви шукаєте:")
    bot.register_next_step_handler(message, process_search_recipe)


def process_search_recipe(message):
    recipes_name = message.text
    db_service = DbService(Session())
    recipes = db_service.search_recipes_by_name(recipes_name)

    if not recipes:
        bot.send_message(message.chat.id, "Рецептів за введеною назвою не знайдено.")
        return

    for recipe in recipes:
        average_rating = db_service.get_average_rating_by_recipe_id(recipe.id)
        average_rating_rounded = round(average_rating, 1) if average_rating is not None else "Немає оцінок"
        formatted_message = f"<b>{recipe.name}</b>\n" \
                            f"Категорія: {', '.join([category.name for category in recipe.categories])}\n" \
                            f"Час приготування: {recipe.cooking_time} хв\n"
        if recipe.url:
            formatted_message += f"URL рецепту: {recipe.url}\n"
        if recipe.image:
            formatted_message += f"Зображення: {recipe.image}\n"
        formatted_message += "Інгредієнти:\n"
        for ingredient in recipe.ingredients:
            formatted_message += f"{ingredient.name}\n"
        if recipe.description:
            formatted_message += f"Опис: {recipe.description}\n"
        formatted_message += f"<b>Середня оцінка:</b> {average_rating_rounded}\n"
        bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')

        ask_for_reviews(message, db_service, recipe)


def ask_for_reviews(message, db_service, recipe):
    markup = types.InlineKeyboardMarkup(row_width=2)
    yes_button = types.InlineKeyboardButton("Так", callback_data=f"review_yes_{recipe.id}")
    no_button = types.InlineKeyboardButton("Ні", callback_data=f"review_no_{recipe.id}")
    markup.add(yes_button, no_button)
    bot.send_message(message.chat.id, "Бажаєте переглянути відгуки для цього рецепту?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def process_review_option(callback_query):
    _, option, recipe_id = callback_query.data.split('_')
    recipe_id = int(recipe_id)
    db_service = DbService(Session())
    recipe = db_service.get_recipe_by_id(recipe_id)
    if option == "yes":
        process_show_reviews_for_single_recipe(callback_query.message, db_service, recipe)
    elif option == "no":
        bot.send_message(callback_query.message.chat.id, "Добре, не показуватиму відгуки.")


def process_show_reviews_for_single_recipe(message, db_service, recipe):
    reviews = db_service.get_reviews_by_recipe_id(recipe.id)
    if not reviews:
        bot.send_message(message.chat.id, "Для цього рецепту ще немає відгуків.")
        return

    bot.send_message(message.chat.id, f"Відгуки для рецепту '{recipe.name}':")
    for review in reviews:
        bot.send_message(message.chat.id, review.text)


@bot.message_handler(commands=['search_by_category'])
def handle_search_recipe(message):
    bot.send_message(message.chat.id,
                     "Введіть назву категорії, для якої ви хочете побачити рецепти(доступні категорії: 'Перші страви', 'Другі страви', 'Салати', 'Закуски', 'Напої', 'Десерти', 'Випічка', 'Інше'):")
    bot.register_next_step_handler(message, process_search_by_category)


def process_search_by_category(message):
    category_name = message.text
    db_service = DbService(Session())
    category = db_service.get_category_by_name(category_name)

    if category:
        recipes = category.recipes
        if recipes:
            bot.send_message(message.chat.id, f"Рецепти з категорії '{category_name}':\n")
            for recipe in recipes:
                average_rating = db_service.get_average_rating_by_recipe_id(recipe.id)
                average_rating_rounded = round(average_rating, 1) if average_rating is not None else "Немає оцінок"
                formatted_message = f"<b>{recipe.name}</b>\n" \
                                    f"Категорія: {', '.join([category.name for category in recipe.categories])}\n" \
                                    f"Час приготування: {recipe.cooking_time} хв\n"
                if recipe.url:
                    formatted_message += f"URL рецепту: {recipe.url}\n"
                if recipe.image:
                    formatted_message += f"Зображення: {recipe.image}\n"
                formatted_message += "Інгредієнти:\n"
                for ingredient in recipe.ingredients:
                    formatted_message += f"{ingredient.name}\n"
                if recipe.description:
                    formatted_message += f"Опис: {recipe.description}\n"
                formatted_message += f"<b>Середня оцінка:</b> {average_rating_rounded}\n"
                bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, f"В категорії '{category_name}' ще немає рецептів.")
    else:
        bot.send_message(message.chat.id, f"Категорії '{category_name}' не існує.")


@bot.message_handler(commands=['random_recipe'])
def handle_get_random_recipe(message):
    try:
        db_service = DbService(Session())
        random_recipe = db_service.get_random_recipe()
        average_rating = db_service.get_average_rating_by_recipe_id(random_recipe.id)
        average_rating_rounded = round(average_rating, 1) if average_rating is not None else "Немає оцінок"

        formatted_message = f"<b>{random_recipe.name}</b>\n" \
                            f"Категорія: {', '.join([category.name for category in random_recipe.categories])}\n" \
                            f"Час приготування: {random_recipe.cooking_time} хв\n"
        if random_recipe.url:
            formatted_message += f"<b>URL рецепту:</b> {random_recipe.url}\n"
        if random_recipe.image:
            formatted_message += f"<b>Зображення:</b> {random_recipe.image}\n"
        formatted_message += "<b>Інгредієнти:</b>\n"
        for ingredient in random_recipe.ingredients:
            formatted_message += f"{ingredient.name}\n"
        if random_recipe.description:
            formatted_message += f"<b>Опис:</b> {random_recipe.description}\n"
        formatted_message += f"<b>Середня оцінка:</b> {average_rating_rounded}\n"
        bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')

    except Exception as e:
        bot.reply_to(message, f"Помилка: {str(e)}")


@bot.message_handler(commands=['rate_recipe'])
def handle_rate_recipe(message):
    bot.send_message(message.chat.id, "Введіть назву рецепту, який ви хочете оцінити:")
    bot.register_next_step_handler(message, process_rate_recipe)


def process_rate_recipe(message):
    recipe_name = message.text
    db_service = DbService(Session())
    recipes = db_service.search_recipes_by_name(recipe_name)

    if not recipes:
        bot.send_message(message.chat.id, "Рецепт з такою назвою не знайдено.")
        return

    if len(recipes) == 1:
        # Якщо знайдено лише один рецепт з цією назвою, продовжуємо обробку
        process_rate_recipe_for_single_recipe(message, db_service, recipes[0])
    else:
        # Виводимо всі знайдені рецепти перед вибором
        bot.send_message(message.chat.id, "Наші рецепти з такою назвою:")
        for recipe in recipes:
            average_rating = db_service.get_average_rating_by_recipe_id(recipe.id)
            average_rating_rounded = round(average_rating, 1) if average_rating is not None else "Немає оцінок"
            formatted_message = f"<b>{recipe.name}</b>\n" \
                                f"Категорія: {', '.join([category.name for category in recipe.categories])}\n" \
                                f"Час приготування: {recipe.cooking_time} хв\n"
            if recipe.url:
                formatted_message += f"URL рецепту: {recipe.url}\n"
            if recipe.image:
                formatted_message += f"Зображення: {recipe.image}\n"
            formatted_message += "Інгредієнти:\n"
            for ingredient in recipe.ingredients:
                formatted_message += f"{ingredient.name}\n"
            if recipe.description:
                formatted_message += f"Опис: {recipe.description}\n"
            formatted_message += f"<b>Середня оцінка:</b> {average_rating_rounded}\n\n"
            bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')

        # Виводимо кнопки для вибору рецепту
        markup = types.InlineKeyboardMarkup(row_width=1)
        for recipe in recipes:
            button = types.InlineKeyboardButton(recipe.name, callback_data=f"rate_{recipe.id}")
            markup.add(button)
        bot.send_message(message.chat.id, "Оберіть потрібний рецепт:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def process_rate_callback(callback_query):
    recipe_id = int(callback_query.data.split('_')[1])
    db_service = DbService(Session())
    recipe = db_service.get_recipe_by_id(recipe_id)
    process_rate_recipe_for_single_recipe(callback_query.message, db_service, recipe)


def process_rate_recipe_for_single_recipe(message, db_service, recipe):
    bot.send_message(message.chat.id, "Введіть вашу оцінку для цього рецепту (від 1 до 5):")
    bot.register_next_step_handler(message, process_rating, db_service, recipe)


def process_rating(message, db_service, recipe):
    try:
        rating_value = int(float(message.text))
        if 1 <= rating_value <= 5:
            new_rating = Rating(value=rating_value, recipe_id=recipe.id)
            db_service.save_ratings([new_rating])
            bot.send_message(message.chat.id, f"Вашу оцінку {rating_value} для рецепту '{recipe.name}' збережено.")
        else:
            bot.send_message(message.chat.id, "Оцінка має бути у межах від 1 до 5.")
    except ValueError:
        bot.send_message(message.chat.id, "Будь ласка, введіть число від 1 до 5.")


@bot.message_handler(commands=['review_recipe'])
def handle_review_recipe(message):
    bot.send_message(message.chat.id, "Введіть назву рецепту, для якого ви хочете залишити відгук:")
    bot.register_next_step_handler(message, process_review_recipe)


def process_review_recipe(message):
    recipe_name = message.text
    db_service = DbService(Session())
    recipes = db_service.search_recipes_by_name(recipe_name)

    if not recipes:
        bot.send_message(message.chat.id, "Рецепт з такою назвою не знайдено.")
        return

    if len(recipes) == 1:
        # Якщо знайдено лише один рецепт з цією назвою, продовжуємо обробку
        process_text_review(message, recipes[0])
    else:
        # Виводимо всі знайдені рецепти перед вибором
        bot.send_message(message.chat.id, "Наші рецепти з такою назвою:")
        for recipe in recipes:
            average_rating = db_service.get_average_rating_by_recipe_id(recipe.id)
            average_rating_rounded = round(average_rating, 1) if average_rating is not None else "Немає оцінок"
            formatted_message = f"<b>{recipe.name}</b>\n" \
                                f"Категорія: {', '.join([category.name for category in recipe.categories])}\n" \
                                f"Час приготування: {recipe.cooking_time} хв\n"
            if recipe.url:
                formatted_message += f"URL рецепту: {recipe.url}\n"
            if recipe.image:
                formatted_message += f"Зображення: {recipe.image}\n"
            formatted_message += "Інгредієнти:\n"
            for ingredient in recipe.ingredients:
                formatted_message += f"{ingredient.name}\n"
            if recipe.description:
                formatted_message += f"Опис: {recipe.description}\n"
            formatted_message += f"<b>Середня оцінка:</b> {average_rating_rounded}\n\n"
            bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')

        # Виводимо кнопки для вибору рецепту
        markup = types.InlineKeyboardMarkup(row_width=1)
        for recipe in recipes:
            button = types.InlineKeyboardButton(recipe.name, callback_data=f"review1_{recipe.id}")
            markup.add(button)
        bot.send_message(message.chat.id, "Оберіть потрібний рецепт для залишення відгуку:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('review1_'))
def process_review_callback(callback_query):
    recipe_id = int(callback_query.data.split('_')[1])
    db_service = DbService(Session())
    recipe = db_service.get_recipe_by_id(recipe_id)
    process_text_review(callback_query.message, recipe)


def process_text_review(message, recipe):
    bot.send_message(message.chat.id, f"Введіть ваш відгук про рецепт '{recipe.name}':")
    bot.register_next_step_handler(message, save_review, recipe)


def save_review(message, recipe):
    review_text = message.text
    db_service = DbService(Session())
    new_review = Review(text=review_text, recipe_id=recipe.id)
    db_service.save_reviews([new_review])
    bot.send_message(message.chat.id, f"Ваш відгук про рецепт '{recipe.name}' збережено.")


@bot.message_handler(func=lambda message: message.text == "/start")
def handle_start(message):
    bot.send_message(message.chat.id,
                     "Привіт! Я тут, щоб допомогти з рецептами. Що б ви хотіли? Натисніть /add_recipe щоб додати рецепт та /search_recipe щоб знайти рецепт або /search_by_category щоб знайти рецепт по категорії яка вас цікавить"
                     "\nВи також можете спробувати щось незвичне з допомогою команди /random_recipe і отримати випадковий рецепт із всіх що доступні мені. \nДодаткові команди та інформацію про них можна отримати з допомогою команди /help")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("/add_recipe")
    item2 = types.KeyboardButton("/search_recipe")
    item3 = types.KeyboardButton("/search_by_category")
    item4 = types.KeyboardButton("/random_recipe")
    item5 = types.KeyboardButton("/rate_recipe")
    item6 = types.KeyboardButton("/review_recipe")
    item7 = types.KeyboardButton("/help")
    markup.add(item1, item2, item3, item4, item5, item6, item7)
    chat_id = message.chat.id
    bot.send_message(chat_id, "Оберіть дію:", reply_markup=markup)


COMMANDS_HELP = {
    "/add_recipe": "Додати новий рецепт."
                   "\nПриклад введення:"
                   "\n'Оберіть одну з доступних категорій'"
                   "\nНазва рецепту: Салат"
                   "\nЧас приготування: 15"
                   "\nURL рецепту: https://example.com/ "
                   "\nабо  -  якщо URL відсутній"
                   "\nURL фото: https://example.com/"
                   "\nабо  -  якщо URL відсутній"
                   "\nІнгредієнти приклад:"
                   "\n200 г томатів чері"
                   "\n1 огірок"
                   "\n1 солодкий перець"
                   "\n50 г оливок без кісточок"
                   "\n200 г сиру фета"
                   "\n1 ч. л. орегано"
                   "\n3 ст. л. оливкової олії"
                   "\nсіль до смаку"
                   "\nі т.д "
                   "\nпісля цього натисніть '/done'"
                   "\nОпис: Введіть опис приготування вашої страви.",
    "\n/search_recipe": "Знайти рецепт за назвою.",
    "\n/search_by_category": "Знайти рецепти за категорією.",
    "\n/random_recipe": "Отримання випадкового рецепту.",
    "\n/rate_recipe": "Поставити оцінку рецепту.",
    "\n/review_recipe": "Написати відгук рецепту.",
    "\n/help": "Вивести список доступних команд разом з описом."

}


@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = "Список доступних команд разом з описом:\n\n"
    for command, description in COMMANDS_HELP.items():
        help_text += f"{command}: {description}\n"
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message,
                 "Я лише бот з рецептами. Якщо вам потрібна допомога з користуванням введіть команду /help")


bot.polling()
