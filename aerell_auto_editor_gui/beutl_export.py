import json
import os
import random
import string
import uuid
from fractions import Fraction

# Beutl (https://github.com/b-editor/beutl) project format, as produced by
# app version 1.1.0. The 2.0 series reorganizes the project layout, so this
# module intentionally targets 1.1.0's `.bep` / `.scene` / `.belm` schema.
BEUTL_APP_VERSION = '1.1.0'
BEUTL_MIN_APP_VERSION = '1.0.0-preview.9'

# Accent color Beutl assigns to a video element added via drag & drop.
VIDEO_ACCENT_COLOR = '#ff99d9da'
# Element.AccentColorProperty's own default (Colors.Teal), used for audio
# elements since no reference sample exists for the audio-only case.
AUDIO_ACCENT_COLOR = '#ff008080'

TICKS_PER_SECOND = 10_000_000


def _new_id() -> str:
    return str(uuid.uuid4())


def _new_belm_id() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=8))


def _to_timecode(seconds: float) -> str:
    total_ticks = round(seconds * TICKS_PER_SECOND)
    sign = '-' if total_ticks < 0 else ''
    total_ticks = abs(total_ticks)

    secs, frac_ticks = divmod(total_ticks, TICKS_PER_SECOND)
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)

    timecode = f'{hours:02d}:{mins:02d}:{secs:02d}'
    if frac_ticks:
        timecode += f'.{frac_ticks:07d}'
    return sign + timecode


def _framerate_str(tb: Fraction) -> str:
    value = float(tb)
    if abs(value - round(value)) < 1e-9:
        return str(round(value))
    return f'{value:.10g}'


def _build_video_belm(*, start_sec, length_sec, offset_sec, speed, z_index, source_path, name) -> dict:
    length_tc = _to_timecode(length_sec)
    return {
        'Start': _to_timecode(start_sec),
        'Length': length_tc,
        'ZIndex': z_index,
        'AccentColor': VIDEO_ACCENT_COLOR,
        'IsEnabled': True,
        'UseNode': False,
        'Id': _new_id(),
        'Name': name,
        'Operation': {
            'Id': _new_id(),
            'Name': '',
            'Children': [
                {
                    'Value': {
                        'OffsetPosition': _to_timecode(offset_sec),
                        'Speed': speed,
                        'Source': source_path,
                        'IsLoop': False,
                        'Transform': {
                            'IsEnabled': True,
                            'Id': _new_id(),
                            'Name': '',
                            'Animations': {},
                            'Children': [],
                            '$type': '[Beutl.Engine]Beutl.Graphics.Transformation:TransformGroup',
                        },
                        'FilterEffect': {
                            'IsEnabled': True,
                            'Id': _new_id(),
                            'Name': '',
                            'Animations': {},
                            'Children': [],
                            '$type': '[Beutl.Engine]Beutl.Graphics.Effects:FilterEffectGroup',
                        },
                        'AlignmentX': 1,
                        'AlignmentY': 1,
                        'TransformOrigin': '50%, 50%',
                        'Fill': None,
                        'OpacityMask': None,
                        'BlendMode': 3,
                        'Opacity': 100,
                        'IsVisible': True,
                        'ZIndex': 0,
                        'TimeRange': {
                            'Start': '00:00:00',
                            'Duration': length_tc,
                            'End': length_tc,
                            'IsEmpty': False,
                        },
                        'Id': _new_id(),
                        'Name': '',
                        'Animations': {},
                        '$type': '[Beutl.Engine]Beutl.Graphics:SourceVideo',
                    },
                    'IsEnabled': True,
                    'Id': _new_id(),
                    'Name': '',
                    '$type': '[Beutl.Operators].Source:SourceVideoOperator',
                }
            ],
        },
        'NodeTree': {
            'Id': _new_id(),
            'Name': '',
            'Nodes': [],
            '$type': '[Beutl.ProjectSystem]Beutl.NodeTree:ElementNodeTreeModel',
        },
    }


def _build_audio_belm(*, start_sec, length_sec, offset_sec, speed, z_index, source_path, name) -> dict:
    length_tc = _to_timecode(length_sec)
    return {
        'Start': _to_timecode(start_sec),
        'Length': length_tc,
        'ZIndex': z_index,
        'AccentColor': AUDIO_ACCENT_COLOR,
        'IsEnabled': True,
        'UseNode': False,
        'Id': _new_id(),
        'Name': name,
        'Operation': {
            'Id': _new_id(),
            'Name': '',
            'Children': [
                {
                    'Value': {
                        'Source': source_path,
                        'OffsetPosition': _to_timecode(offset_sec),
                        'Gain': 100,
                        'Speed': speed,
                        'Effect': {
                            'IsEnabled': True,
                            'Id': _new_id(),
                            'Name': '',
                            'Animations': {},
                            'Children': [],
                            '$type': '[Beutl.Engine]Beutl.Audio.Effects:AudioEffectGroup',
                        },
                        'TimeRange': {
                            'Start': '00:00:00',
                            'Duration': length_tc,
                            'End': length_tc,
                            'IsEmpty': False,
                        },
                        'Id': _new_id(),
                        'Name': '',
                        'Animations': {},
                        '$type': '[Beutl.Engine]Beutl.Audio:SourceSound',
                    },
                    'IsEnabled': True,
                    'Id': _new_id(),
                    'Name': '',
                    '$type': '[Beutl.Operators].Source:SourceSoundOperator',
                }
            ],
        },
        'NodeTree': {
            'Id': _new_id(),
            'Name': '',
            'Nodes': [],
            '$type': '[Beutl.ProjectSystem]Beutl.NodeTree:ElementNodeTreeModel',
        },
    }


def convert_v3_to_beutl(v3_json_path: str, output_path: str) -> str:
    """Convert an auto-editor v3 timeline JSON file into a Beutl 1.1.0
    project rooted at `output_path` (a `.bep` file path). Returns the
    written `.bep` path."""

    with open(v3_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    num_str, den_str = data['timebase'].split('/')
    tb = Fraction(int(num_str), int(den_str))
    width, height = data['resolution']

    output_path = os.path.abspath(output_path)
    if not output_path.lower().endswith('.bep'):
        output_path += '.bep'

    bep_path = output_path
    project_name = os.path.splitext(os.path.basename(bep_path))[0]
    project_dir = os.path.join(os.path.dirname(bep_path), project_name)
    os.makedirs(project_dir, exist_ok=True)

    max_end_sec = 0.0
    z_index = 0

    for layer in data.get('v', []):
        for clip in layer:
            if clip.get('name') != 'video':
                continue

            start_sec = float(clip['start']) / float(tb)
            length_sec = float(clip['dur']) / float(tb)
            offset_sec = float(clip['offset']) / float(tb)
            speed = float(clip.get('speed', 1.0)) * 100.0
            source_path = os.path.abspath(clip['src'])
            max_end_sec = max(max_end_sec, start_sec + length_sec)

            belm = _build_video_belm(
                start_sec=start_sec,
                length_sec=length_sec,
                offset_sec=offset_sec,
                speed=speed,
                z_index=z_index,
                source_path=source_path,
                name=os.path.splitext(os.path.basename(source_path))[0],
            )
            belm_path = os.path.join(project_dir, f'{_new_belm_id()}.belm')
            with open(belm_path, 'w', encoding='utf-8') as bf:
                json.dump(belm, bf, ensure_ascii=False, indent=2)
        z_index += 1

    for layer in data.get('a', []):
        for clip in layer:
            start_sec = float(clip['start']) / float(tb)
            length_sec = float(clip['dur']) / float(tb)
            offset_sec = float(clip['offset']) / float(tb)
            speed = float(clip.get('speed', 1.0)) * 100.0
            source_path = os.path.abspath(clip['src'])
            max_end_sec = max(max_end_sec, start_sec + length_sec)

            belm = _build_audio_belm(
                start_sec=start_sec,
                length_sec=length_sec,
                offset_sec=offset_sec,
                speed=speed,
                z_index=z_index,
                source_path=source_path,
                name=os.path.splitext(os.path.basename(source_path))[0],
            )
            belm_path = os.path.join(project_dir, f'{_new_belm_id()}.belm')
            with open(belm_path, 'w', encoding='utf-8') as bf:
                json.dump(belm, bf, ensure_ascii=False, indent=2)
        z_index += 1

    scene_filename = f'{project_name}.scene'
    scene = {
        'FrameSize': f'{width}, {height}',
        'Start': '00:00:00',
        'Duration': _to_timecode(max_end_sec),
        'Id': _new_id(),
        'Name': project_name,
        'Width': width,
        'Height': height,
        'Elements': {'Include': '**/*.belm'},
    }
    with open(os.path.join(project_dir, scene_filename), 'w', encoding='utf-8') as sf:
        json.dump(scene, sf, ensure_ascii=False, indent=2)

    bep = {
        'Id': _new_id(),
        'Name': '',
        'appVersion': BEUTL_APP_VERSION,
        'minAppVersion': BEUTL_MIN_APP_VERSION,
        'items': [f'{project_name}/{scene_filename}'],
        'variables': {
            'framerate': _framerate_str(tb),
            'samplerate': str(data.get('samplerate', 48000)),
        },
    }
    with open(bep_path, 'w', encoding='utf-8') as pf:
        json.dump(bep, pf, ensure_ascii=False, indent=2)

    beutl_dir = os.path.join(project_dir, '.beutl')
    os.makedirs(beutl_dir, exist_ok=True)
    output_profile = [
        {
            'Extension': '[Beutl].Services.PrimitiveImpls:SceneOutputExtension',
            'File': os.path.join(project_dir, scene_filename),
            'Context': {
                'Name': 'Default',
                'DestinationFile': None,
                'VideoSettings': None,
                'AudioSettings': None,
            },
        }
    ]
    with open(os.path.join(beutl_dir, 'output-profile.json'), 'w', encoding='utf-8') as of:
        json.dump(output_profile, of, ensure_ascii=False)

    return bep_path
