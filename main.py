import database
from ui.main_window import MainWindow


def main():
    database.init_db()
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
