from aerell_auto_editor_gui.ae_arg import AEArgument
from aerell_auto_editor_gui.ae_export_enum import AEExportEnum

class AE():
    def gen(self, arg: AEArgument) -> list[str]:
        if not arg.valid():
            raise ValueError('Incomplete argument.')

        command: list[str] = []

        for inp in arg.inputs:
            command.append(inp)

        edit_parts: list[str] = []
        if arg.audio_threshold is not None:
            edit_parts.append(f'audio:threshold={arg.audio_threshold}')
        if arg.motion_threshold is not None:
            edit_parts.append(f'motion:threshold={arg.motion_threshold}')

        if len(edit_parts) == 1:
            command.extend(['--edit', edit_parts[0]])
        elif len(edit_parts) > 1:
            command.extend(['--edit', f'({" or ".join(edit_parts)})'])

        command.extend(['--margin', f'{arg.margin}s'])

        if arg.export is not None and arg.export != AEExportEnum.NONE:
            command.extend(['--export', arg.export.value[0]])

        if arg.output is not None:
            command.extend(['--output', arg.output])

        return command
