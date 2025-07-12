import database
from ui.main_window import MainWindow


def main():
    # Инициализация базы данных и запуск приложения
    database.init_db()
    database.reset_all_tables()
    database.insert_data()
    app = MainWindow.alloc().init()
    app.run()


if __name__ == "__main__":
    main()
