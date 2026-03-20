Отчет по лабораторной работе N11
**Техническая реализация проекта**

Проект (flaskr/) состоит из трех главных компонент

компонента маршрутизации

компонента базы данных

компонента шаблонов

Экземпляр приложения создается в файле __init__.py.

Маршрутизация

Логика маршрутизации задается с помощью использования чертежей (blueprints) фреймворка Flask, реализованных в одноименной поддиректории.

Задание чертежа происходит созданием экземпляра класса Blueprint (flask) следующим образом

bp = Blueprint('bp_name', __name__, url_prefix='bp_prefix')
Здесь

bp_name - уникальное имя, ассоциируемое с чертежом, в частности позволяющее получать адреса, используя функцию url_for('bp_name.bp_func_name'); url_for - предоставляемая flask функция, bp_func_name - зарегистрированная в чертеже функция, отвечающая за логику обработки запроса при переходе на соответсвующий адрес
bp_prefix - префикс, который будут иметь все адреса, задаваемые логикой функций, отвечающих за маршрутизацию по данному чертежу
Обработка запросов по адресу осуществляется использованием декоратора @bp.route с задаваемыми параметрами path, methods на функциях, реализующих логику обработки запроса.

Пример: регистрация

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register() -> str | Response:
    ...
Функция register обрабатывает логику регистрации пользователя, адрес запроса http://HOST:PORT/auth/register, при этом обрабатываются как GET-запросы (показ формы), так и POST-запросы (отправка данных формы).

Регистрация чертрежей в приложении происходит в фабричой функции методом App.register_blueprint с передачей соответствующего экземпляра чертежа.

База данных

База данных проекта релизована с помощью расширения Flask-SQLAlchemy на основе технологии ORM.

Основа моделей - наследованные от DeclarativeBase (sqlalchemy.orm) класс, регистрирующий подклассы как модели в ORM

class Base(DeclarativeBase):
    pass
Модели находятся в поддиректории models/ и строятся как производные этого класса. Для указания колонок базы данных (послей бизнес моделей) используются аннотаця Mapped (sqlalchemy.orm) и объявление с помощью mapped_column (sqlalchemy.orm).

Модель User

Представляет пользователя сайта.

class User(Base):
    __tablename__ = 'users'

    EMAIL_MAX_LENGTH = 30
    NICKNAME_MIN_LENGTH = 3
    NICKNAME_MAX_LENGTH = 30
    PASSWORD_MAX_LENGTH = 150
    AGE_MIN = 10
    AGE_MAX = 120
    GENRE_MAX_LENGTH = 50

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(NICKNAME_MAX_LENGTH), nullable=False)
    password: Mapped[str] = mapped_column(String(PASSWORD_MAX_LENGTH), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    genre: Mapped[str] = mapped_column(String(GENRE_MAX_LENGTH), nullable=True)
Модель Book

Представляет книгу.

class Book(Base):
    __tablename__ = 'books'

    NAME_MAX_LENGTH = 30
    AUTHOR_MAX_LENGTH = 30
    ANNOTATION_MAX_LENGTH = 500
    GENRE_MAX_LENGTH = 50

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), nullable=False)
    author: Mapped[str] = mapped_column(String(AUTHOR_MAX_LENGTH), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    annotation: Mapped[str] = mapped_column(String(ANNOTATION_MAX_LENGTH), nullable=True)
    genre: Mapped[str] = mapped_column(String(GENRE_MAX_LENGTH), nullable=True)
Модель UserBook

Представляет связь многие-ко-многим между книгами и пользователями, храня информацию о книге, на которую подписан пользователь.

class UserBook(Base):
    __tablename__ = 'user_book'

    RATING_MIN = 1
    RATING_MAX = 10
    REVIEW_MAX_LENGTH = 8192

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey('books.id'), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(REVIEW_MAX_LENGTH), nullable=True)
Создание файла базы данных осуществляется путем передачи пути по ключу SQLALCHEMY_DATABASE_URI конфигигурации, задаваемой параметром-словарем фабричной функции create_app. Если конфигурация не была передана, используются заданные в директории instance/ настройки файла config.py. В текущей реализации путь в базе данных в файле config.py задается таким образом

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
    os.path.dirname(__file__),
    'app_database.db'
)
Создание экземпляра базы данных (настройка движков, очистки соединений и сессий после запросов, ассоциирование моделей и таблиц) происходит конструктором класса SQLAlchemy (flask_sqlalchemy)

def create_db() -> SQLAlchemy:
    return SQLAlchemy(model_class=Base)
Инициализация базы данных осуществляется созданной с декоратором @click.command командой

def init_db_in_app(app: Flask) -> None:
    app.cli.add_command(init_db_command)

@click.command('init-db')
def init_db_command() -> None:
    db: SQLAlchemy = current_app.extensions['db']
    db.create_all()
    count = init_db_with_book_data()
    if count > 0:
        click.echo(f'Initialized DB with {count} books')
    else:
        click.echo(f'DB has already been initialized')
Здесь @click.command('init-db') задает функционал комады flask --app flaskr init-db, которая создает экземпляр приложения (flask --app flaskr) без запуска сервера, вызывая фабричную функцию create_app, регистрирует команду вызовом функции init_db_in_app и выполняет ее, попутно инициализируя базу данных в приложении методом SQLAlchemy.init_app.

Доступ к базе данных в приложении происходит получением соответствующего экземпляра из поля-словаря extensions экземпляра приложения, куда экземпляр базы данных записывается по ключу db.

Запросы к базе данных осуществляются использованием внутреннего API.

Пример: получение книг пользователя

user = db.session.get(User, user_id)
stmt = (
    select(
        Book.id, Book.name, Book.author,
        UserBook.rating, UserBook.review
    )
    .join(UserBook, UserBook.book_id == Book.id)
    .where(UserBook.user_id == user_id)
)
user_books = db.session.execute(stmt).all()
Шаблоны

Все шаблоны реализованы постранично в соответствии с бизнес логикой приложения в поддиректории tamplates/ с использованием следующих инструментов

Jinja2 для динамической генерации html

Flask для генерации адресов (url_for) и передачи данных и обработки шаблонов (render_template)

Bootstrap 5 для создания дизайна приложения

Некоторые стили реализованы в файлах поддиректории static/.

Для однотипной обработки ошибок и уведомлений все шаблоны наследуются от шаблона base.html, где реализуется этот функционал. Замена содержимового ('вставка' шаблона в родительский) происходит в блоке {% block content %}...{% endblock %}.

Фабрика приложения

__init__.py содержит фабричную функцию create_app, создающую экземпляр полноценного приложения.

Приложения создается как экземпляр класса Flask

app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
Последняя строка нужна для создания директории instance/, где находятся файл базы данных и опциональный конфигурационный файл config.py.

Настройки конфигурации приложения (например, путь к базе данных, имя сервера приложения, запуск с опцией отладки) можно задавать как в заранее написанном файле config.py директории instance/, так и передавая параметр test_config фабричной функции, что удобно для тестирования и кастомизации развертывания.

В фабричной функции происходит инициализация и регистрация базы данных и регистрация чертежей.

О процессе реализации
Проблемы, которые у нас возникли
Изначально перед нами стояла проблема найти бесплатное приложение, где мы смогли бы создать uml-диаграммы для понимания над чем работаем, а также возникли небольшие проблемы по распределению задач, так как писать темплейты без возможности посмотреть, как это будет выглядеть на сайте, было непросто.

Кроеме того, было сложно поддерживать консистентность путей между html файлами и путями маршрутизации.

Процесс разработки
В проекте изначально вместе придумывали маршрутизацию и сущности. Дмитрий писал базы данных и маршрутизацию, Виктория и Анастасия занимались созданием сущностей, темплейтсев и CSS.

Задачи проекта написаны в Github Project.

Набросок (отправная точка) проекта

Демонстрация проекта

Описание функционала
Пользователь заходит на сайт и на первой странице видит меню, пользователь проходит регистрацию (заполняет о себе информацию: email, никнейм, возраст, любимый жанр и создает пароль).

После заполнения своих данных пользователь видит приветствие и меню с двумя кнопками: перейти в профиль и посмотреть общий каталог книг.

Дальше у пользователя появляется возможность перейти в свой профиль или посмотреть каталог имеющихся книг.

В своем профиле пользователь может выйти из него, перейти на главную страницу и перейти в каталог, в котором можно добавить книгу в личный каталог, после добавления которой пользователь может добавить оценку от 1 до 10 и написать отзыв, отображающийся на странице книги в общем каталоге.

Книги в базу данных в текущей версии приложения добавляет администратор сайта.

Методология Git flow
Методология была реализована таким образом:

главная ветка - main, куда выгружается итоговый вариант проекта (текущий релиз)

ветка developer является дочерней от main и служит полной кодовой базой, но она не обязательна соответствует текущему релизу

фичи приложения были реализовываны в дочерних от developer ветках feature/*

ветки release/* являются дочерними от developer и служат релизами приложения, которые впоследствии сливаются с main

в дочерних от main ветках patch/* делается hot fix текущего релиза