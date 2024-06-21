from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql://root:dfdfdf123@localhost:3306/recipe_tgbot')

Session = sessionmaker(bind=engine)

Base = declarative_base()
