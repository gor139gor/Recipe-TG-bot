import sqlalchemy
from sqlalchemy.sql.expression import func
from models.models import Recipe, Ingredient, Category, recipes_categories_table, Rating, Review
from typing import List


class DbService:
    def __init__(self, session):
        self._session = session

    def save_recipes(self, data: List):
        if not data:
            return
        data.reverse()

        for recipe_data in data:
            if type(recipe_data) is Recipe:
                recipe = recipe_data
            else:
                recipe_data["ingredients"] = [Ingredient(
                    **ingredient_data) for ingredient_data in recipe_data["ingredients"]]
                recipe = Recipe(**recipe_data)
            self._session.add(recipe)

        self._session.commit()

    def save_recipes_categories(self, rows: List[dict]):
        for row in rows:
            stmt = recipes_categories_table.insert().values(**row)
            self._session.execute(stmt)
        self._session.commit()

    def get_all_urls(self):
        return [*map(
            lambda row: row[0],
            self._session.query(Recipe.url).all()
        )]

    def get_all_recipes(self):
        return self._session.query(Recipe).all()

    def get_random_recipe(self):
        return self._session.query(Recipe).order_by(func.random()).first()

    def save_categories(self, categories):
        self._session.add_all(categories)
        self._session.commit()

    def get_category_by_name(self, category_name):
        return self._session.query(Category).filter_by(name=category_name).first()

    def save_category(self, name):
        category = Category(name=name)
        self._session.add(category)
        self._session.commit()

    def update_category(self, category_id, name=None):
        category = self._session.query(Category).get(category_id)
        if category:
            if name:
                category.name = name
            self._session.commit()

    def get_all_categories(self):
        return self._session.query(Category).all()

    def get_by_url(self, url):
        return self._session.query(Recipe).filter(Recipe.url == url).first()

    def get_recipe_by_id(self, id):
        return self._session.query(Recipe).filter(Recipe.id == id).first()

    def search_recipes_by_name(self, recipes_name):
        recipes = self._session.query(Recipe).filter(Recipe.name.ilike(f"%{recipes_name}%")).options(
            sqlalchemy.orm.subqueryload(Recipe.ingredients)
        ).all()

        return recipes

    def recipe_exists(self, recipe_name):
        return self._session.query(Recipe).filter(Recipe.name.ilike(recipe_name)).count() > 0

    def save_ratings(self, ratings):
        try:
            for rating in ratings:
                self._session.add(rating)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def save_reviews(self, reviews):
        try:
            for review in reviews:
                self._session.add(review)
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise e

    def get_ratings_by_recipe(self, recipe_id):
        try:
            rating = self._session.query(Rating).filter_by(recipe_id=recipe_id).all()
            return rating
        except Exception as e:
            raise e

    def get_average_rating_by_recipe_id(self, recipe_id):
        try:
            average_rating = self._session.query(func.avg(Rating.value)).filter(
                Rating.recipe_id == recipe_id).scalar()
            return average_rating
        except Exception as e:
            raise e

    def get_reviews_by_recipe_id(self, recipe_id):
        try:
            reviews = self._session.query(Review).filter_by(recipe_id=recipe_id).all()
            return reviews
        except Exception as e:
            raise e
