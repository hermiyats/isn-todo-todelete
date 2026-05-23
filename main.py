from controller.board_controller import BoardController
from view.main_window import MainWindow


def main():
    controller = BoardController()
    app = MainWindow(controller)
    app.mainloop()


if __name__ == "__main__":
    main()
