from aerell_auto_editor_gui.ae_arg import AEArgument
from aerell_auto_editor_gui.ae_export_enum import AEExportEnum

class AE():
    def gen(self, arg: AEArgument) -> list[str]:
        if not arg.valid():
            raise ValueError('Incomplete argument.')

        command: list[str] = []

        for inp in arg.inputs:
            command.append(inp)

        command.extend(self._edit_and_margin_args(arg))

        if arg.export is not None and arg.export not in (AEExportEnum.NONE, AEExportEnum.BEUTL):
            command.extend(['--export', arg.export.value[0]])

        if arg.output is not None:
            command.extend(['--output', arg.output])

        return command

    def gen_beutl_intermediate(self, arg: AEArgument, json_output: str) -> list[str]:
        """Build the auto-editor CLI args that produce the v3 timeline JSON
        used as the source of truth for the Beutl project export. auto-editor
        has no native Beutl exporter, so Beutl support works by asking
        auto-editor for its own v3 timeline JSON, then converting that
        timeline into a Beutl project (see beutl_export.py)."""
        if not arg.valid():
            raise ValueError('Incomplete argument.')

        command: list[str] = []

        for inp in arg.inputs:
            command.append(inp)

        command.extend(self._edit_and_margin_args(arg))
        command.extend(['--export', 'v3'])
        command.extend(['--output', json_output])

        return command

    def _edit_and_margin_args(self, arg: AEArgument) -> list[str]:
        command: list[str] = []

        edit_parts: list[str] = []
        if arg.audio_threshold is not None:
            edit_parts.append(f'audio:threshold={arg.audio_threshold}')
        if arg.motion_threshold is not None:
            edit_parts.append(f'motion:threshold={arg.motion_threshold}')

        if len(edit_parts) == 1:
            command.extend(['--edit', edit_parts[0]])
        elif len(edit_parts) > 1:
            command.extend(['--edit', f'(or {" ".join(edit_parts)})'])

        command.extend(['--margin', f'{arg.margin}s'])

        return command
