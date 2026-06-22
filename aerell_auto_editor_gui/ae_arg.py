from aerell_auto_editor_gui.ae_export_enum import AEExportEnum

class AEArgument():
    def __init__(
            self,
            inputs: list[str] | None = None,
            export: AEExportEnum | None = None,
            output: str | None = None,
            audio_threshold: float | None = 0.04,
            motion_threshold: float | None = None,
            margin: float = 0.2,
    ):
        self._inputs: list[str] = inputs if inputs is not None else []

        # Editing Options
        self._export: AEExportEnum | None = export
        self._output: str | None = output
        self._audio_threshold: float | None = audio_threshold
        self._motion_threshold: float | None = motion_threshold
        self._margin: float = margin

    def clear(self):
        self._inputs = []
        self._export = None
        self._output = None
        self._audio_threshold = 0.04
        self._motion_threshold = None
        self._margin = 0.2

    def valid(self) -> bool:
        return len(self._inputs) > 0

    @property
    def inputs(self) -> list[str]:
        return self._inputs

    @property
    def export(self) -> AEExportEnum | None:
        return self._export

    @property
    def output(self) -> str | None:
        return self._output

    @property
    def audio_threshold(self) -> float | None:
        return self._audio_threshold

    @property
    def motion_threshold(self) -> float | None:
        return self._motion_threshold

    @property
    def margin(self) -> float:
        return self._margin

    @inputs.setter
    def inputs(self, value: list[str]):
        self._inputs = value

    @export.setter
    def export(self, value: AEExportEnum | None):
        self._export = value

    @output.setter
    def output(self, value: str | None):
        self._output = value

    @audio_threshold.setter
    def audio_threshold(self, value: float | None):
        self._audio_threshold = value

    @motion_threshold.setter
    def motion_threshold(self, value: float | None):
        self._motion_threshold = value

    @margin.setter
    def margin(self, value: float):
        self._margin = value
