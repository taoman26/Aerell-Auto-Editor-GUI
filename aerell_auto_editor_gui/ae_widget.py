import os
from aerell_auto_editor_gui.ae_export_enum import AEExportEnum
from aerell_auto_editor_gui.ae_arg import AEArgument
from aerell_auto_editor_gui.ae import AE
from aerell_auto_editor_gui.ae_worker import AEWorker
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QDoubleSpinBox,
    QPlainTextEdit,
)

class AEWidget(QWidget):
    def __init__(self, ae: AE, arg: AEArgument):
        super().__init__()

        self._ae = ae
        self._arg = arg
        self._worker: AEWorker | None = None

        layout = QVBoxLayout(self)

        # ── Files ──────────────────────────────────────────────
        label_title_file = QLabel('Files')
        label_title_file.setStyleSheet('font-weight: bold;')

        self._list_files = QListWidget()
        self._list_files.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list_files.setFixedHeight(120)

        button_import = QPushButton('Import')
        button_import.clicked.connect(self._button_import_clicked)

        self._button_remove = QPushButton('Remove')
        self._button_remove.clicked.connect(self._button_remove_clicked)

        self._button_up = QPushButton('↑')
        self._button_up.setFixedWidth(32)
        self._button_up.clicked.connect(self._button_up_clicked)

        self._button_down = QPushButton('↓')
        self._button_down.setFixedWidth(32)
        self._button_down.clicked.connect(self._button_down_clicked)

        layout_file_buttons = QHBoxLayout()
        layout_file_buttons.addWidget(button_import)
        layout_file_buttons.addWidget(self._button_remove)
        layout_file_buttons.addWidget(self._button_up)
        layout_file_buttons.addWidget(self._button_down)
        widget_file_buttons = QWidget()
        widget_file_buttons.setLayout(layout_file_buttons)

        # ── Editing Options ────────────────────────────────────
        label_title_editing = QLabel('Editing Options')
        label_title_editing.setStyleSheet('font-weight: bold;')

        # Export
        layout_export = QHBoxLayout()
        layout_export.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_export = QLabel('Export')
        self._combo_export = QComboBox()
        for enum in AEExportEnum:
            self._combo_export.addItem(enum.value[0])
        self._combo_export.currentIndexChanged.connect(self._combo_export_changed)
        self._combo_export.setCurrentIndex(0)
        layout_export.addWidget(label_export)
        layout_export.addWidget(self._combo_export)
        widget_export = QWidget()
        widget_export.setLayout(layout_export)

        # Silent Cut (audio threshold)
        layout_audio = QHBoxLayout()
        layout_audio.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._check_audio = QCheckBox('Silent Cut')
        self._check_audio.setChecked(True)
        self._check_audio.checkStateChanged.connect(self._check_audio_changed)
        self._spin_audio = QDoubleSpinBox()
        self._spin_audio.setRange(0.0, 1.0)
        self._spin_audio.setSingleStep(0.01)
        self._spin_audio.setDecimals(2)
        self._spin_audio.setValue(0.04)
        self._spin_audio.valueChanged.connect(self._spin_audio_changed)
        layout_audio.addWidget(self._check_audio)
        layout_audio.addWidget(QLabel('Threshold'))
        layout_audio.addWidget(self._spin_audio)
        widget_audio = QWidget()
        widget_audio.setLayout(layout_audio)

        # Motion Cut (motion threshold)
        layout_motion = QHBoxLayout()
        layout_motion.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._check_motion = QCheckBox('Motion Cut')
        self._check_motion.setChecked(False)
        self._check_motion.checkStateChanged.connect(self._check_motion_changed)
        self._spin_motion = QDoubleSpinBox()
        self._spin_motion.setRange(0.0, 1.0)
        self._spin_motion.setSingleStep(0.01)
        self._spin_motion.setDecimals(2)
        self._spin_motion.setValue(0.02)
        self._spin_motion.setEnabled(False)
        self._spin_motion.valueChanged.connect(self._spin_motion_changed)
        layout_motion.addWidget(self._check_motion)
        layout_motion.addWidget(QLabel('Threshold'))
        layout_motion.addWidget(self._spin_motion)
        widget_motion = QWidget()
        widget_motion.setLayout(layout_motion)

        # Margin
        layout_margin = QHBoxLayout()
        layout_margin.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._spin_margin = QDoubleSpinBox()
        self._spin_margin.setRange(0.0, 99.9)
        self._spin_margin.setSingleStep(0.1)
        self._spin_margin.setDecimals(1)
        self._spin_margin.setValue(0.2)
        self._spin_margin.valueChanged.connect(self._spin_margin_changed)
        layout_margin.addWidget(QLabel('Margin'))
        layout_margin.addWidget(self._spin_margin)
        layout_margin.addWidget(QLabel('sec'))
        widget_margin = QWidget()
        widget_margin.setLayout(layout_margin)

        # ── Execute ────────────────────────────────────────────
        self._button_execute = QPushButton('Execute')
        self._button_execute.setDisabled(True)
        self._button_execute.clicked.connect(self._button_execute_clicked)

        # ── Output area ────────────────────────────────────────
        self._output_area = QPlainTextEdit()
        self._output_area.setReadOnly(True)
        self._output_area.setMinimumHeight(150)

        # ── Assemble ───────────────────────────────────────────
        layout.addWidget(label_title_file)
        layout.addWidget(self._list_files)
        layout.addWidget(widget_file_buttons)
        layout.addWidget(label_title_editing)
        layout.addWidget(widget_export)
        layout.addWidget(widget_audio)
        layout.addWidget(widget_motion)
        layout.addWidget(widget_margin)
        layout.addWidget(self._button_execute)
        layout.addWidget(self._output_area)

        self.setLayout(layout)

        # Sync initial arg state
        self._arg.audio_threshold = self._spin_audio.value()
        self._arg.motion_threshold = None
        self._arg.margin = self._spin_margin.value()

    # ── File list helpers ──────────────────────────────────────

    def _update_arg_inputs(self):
        inputs = []
        for i in range(self._list_files.count()):
            item = self._list_files.item(i)
            inputs.append(item.data(Qt.ItemDataRole.UserRole))
        self._arg.inputs = inputs
        self._button_execute_update()

    def _button_import_clicked(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Import media', '', '(*.mp4 *.mov *.m4a)')
        for path in paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self._list_files.addItem(item)
        if paths:
            self._update_arg_inputs()

    def _button_remove_clicked(self):
        row = self._list_files.currentRow()
        if row >= 0:
            self._list_files.takeItem(row)
            self._update_arg_inputs()

    def _button_up_clicked(self):
        row = self._list_files.currentRow()
        if row > 0:
            item = self._list_files.takeItem(row)
            self._list_files.insertItem(row - 1, item)
            self._list_files.setCurrentRow(row - 1)
            self._update_arg_inputs()

    def _button_down_clicked(self):
        row = self._list_files.currentRow()
        if row >= 0 and row < self._list_files.count() - 1:
            item = self._list_files.takeItem(row)
            self._list_files.insertItem(row + 1, item)
            self._list_files.setCurrentRow(row + 1)
            self._update_arg_inputs()

    # ── Editing option callbacks ───────────────────────────────

    def _combo_export_changed(self, index):
        self._arg.export = list(AEExportEnum)[index]
        self._button_execute_update()

    def _check_audio_changed(self, state):
        enabled = state == Qt.CheckState.Checked
        self._spin_audio.setEnabled(enabled)
        self._arg.audio_threshold = self._spin_audio.value() if enabled else None

    def _spin_audio_changed(self, value: float):
        self._arg.audio_threshold = value

    def _check_motion_changed(self, state):
        enabled = state == Qt.CheckState.Checked
        self._spin_motion.setEnabled(enabled)
        self._arg.motion_threshold = self._spin_motion.value() if enabled else None

    def _spin_motion_changed(self, value: float):
        self._arg.motion_threshold = value

    def _spin_margin_changed(self, value: float):
        self._arg.margin = value

    # ── Execute ────────────────────────────────────────────────

    def _button_execute_clicked(self):
        args = self._ae.gen(self._arg)

        self._output_area.clear()
        self._output_area.appendPlainText('$ auto-editor ' + ' '.join(args))
        self._output_area.appendPlainText('')

        self._button_execute.setDisabled(True)

        self._worker = AEWorker(args)
        self._worker.line_output.connect(self._on_worker_output)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_output(self, line: str):
        self._output_area.appendPlainText(line)

    def _on_worker_finished(self, returncode: int):
        if returncode == 0:
            self._output_area.appendPlainText('\nDone.')
        else:
            self._output_area.appendPlainText(f'\nFailed (exit code: {returncode})')
        self._button_execute.setDisabled(False)

    def _button_execute_update(self):
        if hasattr(self, '_button_execute'):
            self._button_execute.setDisabled(not self._arg.valid())
