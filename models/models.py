from sqlalchemy import Column, String, Integer, Table, DateTime, ForeignKey, func, Text, Enum
from mysqlbase import Base
from sqlalchemy.orm import relationship

# Оголошення таблиць зв'язків
recipes_ingredients_table = Table('recipes_ingredients', Base.metadata,
                                  Column('id', Integer, primary_key=True, autoincrement=True),
                                  Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete="CASCADE")),
                                  Column('ingredient_id', Integer, ForeignKey('ingredients.id', ondelete="CASCADE"))
                                  )

recipes_categories_table = Table('recipes_categories', Base.metadata,
                                 Column('id', Integer, primary_key=True, autoincrement=True),
                                 Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete="CASCADE")),
                                 Column('category_id', Integer, ForeignKey('categories.id', ondelete="CASCADE"))
                                 )


class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column('name', String(256))
    cooking_time = Column('cooking_time', Integer)
    url = Column('url', String(256), unique=True)
    image = Column('image', String(256))
    description = Column('description', Text)

    # Визначення зв'язків з іншими таблицями
    ingredients = relationship(
        "Ingredient",
        secondary=recipes_ingredients_table,
        back_populates="recipes",
        cascade="all, delete",
    )
    categories = relationship(
        "Category",
        secondary=recipes_categories_table,
        back_populates="recipes",
        cascade="all, delete",
    )

    ratings = relationship("Rating", back_populates="recipe", cascade="all, delete")
    reviews = relationship("Review", back_populates="recipe", cascade="all, delete")

    def __repr__(self):
        return self.name

    def __str__(self):
        ingredients_str = '\n'.join(map(str, self.ingredients))
        return f'<b>{self.name}</b>\nЧас приготування: {self.cooking_time} хв\n' \
               f'<b>URL:</b> {self.url}\n' \
               f'<b>Зображення:</b> {self.image}\n' \
               f'<b>Інгредієнти:</b>\n{ingredients_str}' \
               f'<b>Опис:</b>\n{self.description}'


class Ingredient(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column('name', String(256))

    # Зв'язок з рецептами
    recipes = relationship(
        "Recipe",
        secondary=recipes_ingredients_table,
        back_populates="ingredients",
        passive_deletes=True
    )

    def __repr__(self):
        return f"{self.name}"


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column('name',
                  Enum('Перші страви', 'Другі страви', 'Салати', 'Закуски', 'Напої', 'Десерти', 'Випічка', 'Інше'))

    # Зв'язок з рецептами
    recipes = relationship(
        "Recipe",
        secondary=recipes_categories_table,
        back_populates="categories",
        cascade="all, delete",
    )

    def __repr__(self):
        return self.name


class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Integer, nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id'))

    recipe = relationship("Recipe", back_populates="ratings")


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id'))

    recipe = relationship("Recipe", back_populates="reviews")
