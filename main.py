"""
https://docs.sqlalchemy.org/en/14/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it

As a general rule, the application should manage the lifecycle of the session externally to functions
that deal with specific data. This is a fundamental separation of concerns
which keeps data-specific operations agnostic of the context in which they access and manipulate that data.
"""

import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import json

from models import Base
from models import Publisher, Book, Shop, Stock, Sale

data_sources = {
    'postgresql':
        # user: [databases]
        {'postgres': ['books_shop']},
    'mysql':
        # user: [databases]
        {'None': ['None']},
}

db_models_map = {
    'publisher': Publisher,
    'book': Book,
    'shop': Shop,
    'stock': Stock,
    'sale': Sale
}

data_file_path = 'db_data/db_data.json'


def create_db_engine(protocol, user, db_name, host='localhost', port=5432):
    with open(f'info_not_for_git/{protocol}/users/{user}.json') as f:
        f_data = json.load(f)
    user_pass = f_data['pass']

    DSN = f'{protocol}://{user}:{user_pass}@{host}:{port}/{db_name}'
    engine = sq.create_engine(DSN)

    return engine


def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


# Функция не подключается к БД !
# Все действия с БД происходят "извне" в блоке main()
def create_models_from_json(file_path, db_map):
    with open(file_path) as f:
        models = json.load(f)

    db_models_list = []
    for model in models:
        data_model = db_map[model["model"]](id=model["pk"], **model["fields"])
        db_models_list.append(data_model)
        return db_models_list

    # with db_session:
    #     for model in models:
    #         data_model = db_map[model["model"]](id=model["pk"], **model["fields"])
    #         db_session.add(data_model)
    #     try:
    #         db_session.commit()
    #     except IntegrityError:
    #         print('Вставка данных из файла: данные уже есть в БД !')


def get_shops_by_publisher_name(publisher_name, db_session):
    publishers = db_session.query(Publisher).filter(Publisher.name.ilike(f'%{publisher_name}%')).all()
    if publishers:
        if len(publishers) == 1:
            print(f'Найден издатель: {publishers[0]}')
            publisher_id = publishers[0].id
            shops = db_session.query(Shop).join(Stock).join(Book).join(Publisher).filter(
                Publisher.id == publisher_id).filter(Stock.count > 0).all()
            return shops
        else:
            print('Найдено более 1 издателя. Пожалуйста, уточните запрос!')
    else:
        print('Издатели не найдены. Пожалуйста, уточните запрос!')


def main():
    # Задаем параметры, необходимые для подключения к СУБД
    data_source_name = 'postgresql'
    db_user = 'postgres'
    db_name = data_sources[data_source_name][db_user][0]
    # Создаем "движок" БД
    engine = create_db_engine(data_source_name, db_user, db_name)
    # Создаем таблицы БД
    create_tables(engine)
    # Создаем сессию с БД
    Session = sessionmaker(bind=engine)
    session = Session()
    # Заполняем таблицы данными из ".json" файла
    # Открываем сессию с БД
    with session:
        # session.begin()
        # Транзакция внутри блока "try...exept"
        try:
            rows_to_insert = create_models_from_json(data_file_path, db_models_map)
            session.add_all(rows_to_insert)
            session.commit()
        except IntegrityError:
            session.rollback()
            print('Вставка данных из файла: данные уже есть в БД !')

        # Находим список магазинов, продающих целевого издателя
        print('Найдем список магазинов, продающих целевого издателя')
        publisher_name = input('Введите часть имени издателя: ')
        # session = Session()
        # with session:
        shops = get_shops_by_publisher_name(publisher_name, session)
        if shops:
            print('Магазины, в которых продаются книги (есть в наличии) выбранного издателя: ')
            for shop in shops:
                print(shop)
        else:
            print('Магазины не найдены!')


if __name__ == '__main__':
    main()
