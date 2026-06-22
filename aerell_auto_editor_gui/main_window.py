from aerell_auto_editor_gui import APP_NAME, APP_VERSION
from aerell_auto_editor_gui.ae_widget import AEWidget
from aerell_auto_editor_gui.ae_arg import AEArgument
from aerell_auto_editor_gui.ae import AE
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout
)

class MainWindow(QMainWindow):
    def __init__(self, ae: AE, arg: AEArgument):
        super().__init__()

        self.setWindowTitle(f'{APP_NAME} - {APP_VERSION}')
        self.resize(500, 620)

        layout = QHBoxLayout()

        widget_ae = AEWidget(ae=ae, arg=arg)

        layout.addWidget(widget_ae)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)