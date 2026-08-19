import json
import os
from fractions import Fraction
from math import gcd
from uuid import uuid4
import xml.etree.ElementTree as ET

# Kdenlive/MLT project export.
#
# auto-editor ships its own kdenlive exporter (auto_editor.exports.kdenlive),
# but it assumes every clip within a track shares one source file: it only
# registers the *first* clip's path per track in its `source_ids` map, then
# looks up every clip's own path in that map when writing playlist entries.
# As soon as a track mixes clips from more than one input file (this app's
# core multi-file feature), that lookup raises `KeyError`. This module
# reimplements the export per-clip (each clip gets its own chain/producer
# tied to its own source path) so multi-file timelines work correctly.


def _aspect_ratio(width: int, height: int) -> tuple[int, int]:
    if height == 0:
        return (0, 0)
    g = gcd(width, height)
    return width // g, height // g


# Kdenlive/MLT only accept integer fps or the three canonical NTSC
# fractions as a project profile's frame rate (ProfileInfo::hasValidFps() in
# Kdenlive's source). auto-editor's v3 timebase, especially once multiple
# source files with different native rates are combined, can come out as an
# arbitrary fraction (e.g. 2963/100), which Kdenlive rejects with a "non
# standard framerate" error and then fails to load the project. Clip
# positions in this file are written as real-time timecodes (see
# _to_timecode below), not as frame counts against this profile, so
# snapping only the declared profile fps to something Kdenlive accepts does
# not affect edit accuracy.
_NTSC_FRACTIONS = ((24000, 1001), (30000, 1001), (60000, 1001))


def _profile_fps(tb: Fraction) -> tuple[int, int]:
    fps = float(tb)
    if fps == int(fps):
        return int(fps), 1
    for num, den in _NTSC_FRACTIONS:
        if abs(fps - num / den) < 0.05:
            return num, den
    return round(fps), 1


def _to_timecode(seconds: float) -> str:
    sign = '-' if seconds < 0 else ''
    seconds = abs(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f'{sign}{h:02d}:{m:02d}:{float(s):06.3f}'


def _prop(parent: ET.Element, name: str, text: str) -> None:
    ET.SubElement(parent, 'property', name=name).text = text


class _IdAllocator:
    def __init__(self, start: int):
        self._next = start
        self._ids: dict[str, str] = {}

    def get(self, path: str) -> str:
        if path not in self._ids:
            self._ids[path] = str(self._next)
            self._next += 1
        return self._ids[path]


def _build_track(
    mlt: ET.Element,
    clips: list[dict],
    tb: Fraction,
    global_out: str,
    *,
    kind: str,  # 'video' or 'audio'
    track_index: int,
    source_ids: _IdAllocator,
    element_counter: list,
    playlist_counter: list,
) -> ET.Element:
    # Kdenlive models each timeline track as a tractor wrapping exactly two
    # playlists (a Kdenlive/MLT convention, seen e.g. in KdenliveDoc::
    # createEmptyDocument, which always inserts two playlists per track).
    # A tractor with only one <track> is treated as corrupted ("wrong
    # number of subtracks") and Kdenlive segfaults shortly after trying to
    # recover it. All clip entries go in the first playlist; the second is
    # kept empty, matching what real Kdenlive/auto-editor output does.
    is_video = kind == 'video'
    playlist_id = f'playlist{playlist_counter[0]}'
    playlist = ET.SubElement(mlt, 'playlist', id=playlist_id)
    if not is_video:
        _prop(playlist, 'kdenlive:audio_track', '1')
    playlist_counter[0] += 1
    blank_playlist_id = f'playlist{playlist_counter[0]}'
    blank_playlist = ET.SubElement(mlt, 'playlist', id=blank_playlist_id)
    if not is_video:
        _prop(blank_playlist, 'kdenlive:audio_track', '1')
    playlist_counter[0] += 1

    # Clips that share a source file at normal speed reuse a single chain
    # (their kdenlive:id / stream-masking properties are identical), the
    # same way a genuine Kdenlive project only has one bin producer per
    # source file rather than one per cut. Speed-warped clips still get
    # their own dedicated producer per instance, since warp_speed differs.
    path_chain_cache: dict[str, str] = {}

    position = 0
    for clip in sorted(clips, key=lambda c: c['start']):
        if clip['start'] > position:
            gap = (clip['start'] - position) / tb
            ET.SubElement(playlist, 'blank', length=_to_timecode(gap))
        position = clip['start'] + clip['dur']

        path = os.path.abspath(clip['src'])
        speed = float(clip.get('speed', 1.0))
        source_id = source_ids.get(path)

        if speed == 1.0 and path in path_chain_cache:
            element_id = path_chain_cache[path]
        else:
            element_id = f'element{element_counter[0]}'
            element_counter[0] += 1

            if speed == 1.0:
                element = ET.SubElement(mlt, 'chain', id=element_id)
                path_chain_cache[path] = element_id
            else:
                element = ET.SubElement(
                    mlt, 'producer', id=element_id, attrib={'in': '00:00:00.000', 'out': global_out}
                )
                _prop(element, 'warp_speed', str(speed))
                _prop(element, 'warp_resource', path)
                _prop(element, 'warp_pitch', '0')

            resource = path if speed == 1.0 else f'{speed}:{path}'
            _prop(element, 'resource', resource)
            _prop(element, 'mlt_service', 'timewarp' if speed != 1.0 else 'avformat-novalidate')
            _prop(element, 'vstream', '0')
            _prop(element, 'astream', '0')
            _prop(element, 'set.test_audio', '1' if is_video else '0')
            _prop(element, 'set.test_video', '0' if is_video else '1')
            _prop(element, 'kdenlive:id', source_id)

        in_tc = _to_timecode(clip['offset'] / tb)
        out_tc = _to_timecode((clip['offset'] + clip['dur']) / tb)
        entry = ET.SubElement(
            playlist, 'entry', attrib={'producer': element_id, 'in': in_tc, 'out': out_tc}
        )
        _prop(entry, 'kdenlive:id', source_id)

    tractor = ET.SubElement(
        mlt,
        'tractor',
        attrib={'id': f'tractor{track_index}', 'in': '00:00:00.000', 'out': global_out},
    )
    if not is_video:
        _prop(tractor, 'kdenlive:audio_track', '1')
    _prop(tractor, 'kdenlive:timeline_active', '1')
    hide = 'audio' if is_video else 'video'
    ET.SubElement(tractor, 'track', attrib={'hide': hide, 'producer': playlist_id})
    ET.SubElement(tractor, 'track', attrib={'hide': hide, 'producer': blank_playlist_id})
    return tractor


def convert_v3_to_kdenlive(v3_json_path: str, output_path: str) -> str:
    """Convert an auto-editor v3 timeline JSON file into a Kdenlive (MLT)
    project. Returns the written `.kdenlive` path."""

    with open(v3_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    num_str, den_str = data['timebase'].split('/')
    tb = Fraction(int(num_str), int(den_str))
    width, height = data['resolution']

    video_clips = [c for c in (data.get('v') or [[]])[0] if c.get('name') == 'video']
    audio_clips = list((data.get('a') or [[]])[0])

    if not video_clips and not audio_clips:
        raise ValueError('Timeline has no clips to export.')

    output_path = os.path.abspath(output_path)
    if not output_path.lower().endswith('.kdenlive'):
        output_path += '.kdenlive'

    total_frames = max(
        [c['start'] + c['dur'] for c in video_clips + audio_clips], default=0
    )
    global_out = _to_timecode(total_frames / tb)

    mlt = ET.Element(
        'mlt',
        {
            'LC_NUMERIC': 'C',
            'version': '7.22.0',
            'producer': 'main_bin',
            'root': os.getcwd(),
        },
    )

    num, den = _aspect_ratio(width, height)
    profile_fps_num, profile_fps_den = _profile_fps(tb)
    ET.SubElement(
        mlt,
        'profile',
        {
            'description': 'automatic',
            'width': str(width),
            'height': str(height),
            'progressive': '1',
            'sample_aspect_num': '1',
            'sample_aspect_den': '1',
            'display_aspect_num': str(num),
            'display_aspect_den': str(den),
            'frame_rate_num': str(profile_fps_num),
            'frame_rate_den': str(profile_fps_den),
            'colorspace': '709',
        },
    )

    producer0 = ET.SubElement(mlt, 'producer', id='producer0')
    _prop(producer0, 'length', global_out)
    _prop(producer0, 'eof', 'continue')
    _prop(producer0, 'resource', 'black')
    _prop(producer0, 'mlt_service', 'color')
    _prop(producer0, 'kdenlive:playlistid', 'black_track')
    _prop(producer0, 'mlt_image_format', 'rgba')
    _prop(producer0, 'aspect_ratio', '1')

    # Reserve main_bin's position as the *first* <playlist> element in the
    # file now (filled in below, once the sequence uuid is known). Kdenlive
    # locates kdenlive:docproperties.version via mlt.firstChildElement
    # ("playlist") — the first <playlist> in document order — so if a
    # per-track playlist ends up first instead, Kdenlive can't find the
    # version property and refuses to open the project.
    playlist_bin = ET.SubElement(mlt, 'playlist', id='main_bin')

    source_ids = _IdAllocator(start=4)
    element_counter = [0]
    playlist_counter = [0]
    track_index = 0
    sequence_tracks: list[str] = []

    if audio_clips:
        tractor = _build_track(
            mlt, audio_clips, tb, global_out,
            kind='audio', track_index=track_index,
            source_ids=source_ids, element_counter=element_counter,
            playlist_counter=playlist_counter,
        )
        sequence_tracks.append(tractor.get('id'))
        track_index += 1

    if video_clips:
        tractor = _build_track(
            mlt, video_clips, tb, global_out,
            kind='video', track_index=track_index,
            source_ids=source_ids, element_counter=element_counter,
            playlist_counter=playlist_counter,
        )
        sequence_tracks.append(tractor.get('id'))
        track_index += 1

    # Register every distinct source file as its own project-bin clip (a
    # plain chain, independent of the stream-masked ones used on tracks).
    # Kdenlive resolves clip metadata/thumbnails for a kdenlive:id through
    # its bin model; a clip whose id has no bin entry left the monitor
    # unable to resolve it and hung generating a thumbnail for it.
    bin_element_ids: list[str] = []
    seen_bin_paths: set[str] = set()
    for clip in video_clips + audio_clips:
        path = os.path.abspath(clip['src'])
        if path in seen_bin_paths:
            continue
        seen_bin_paths.add(path)

        element_id = f'element{element_counter[0]}'
        element_counter[0] += 1
        bin_chain = ET.SubElement(mlt, 'chain', id=element_id)
        _prop(bin_chain, 'resource', path)
        _prop(bin_chain, 'mlt_service', 'avformat-novalidate')
        _prop(bin_chain, 'kdenlive:id', source_ids.get(path))
        bin_element_ids.append(element_id)

    seq_uuid = uuid4()
    sequence = ET.SubElement(
        mlt,
        'tractor',
        attrib={'id': f'{{{seq_uuid}}}', 'in': '00:00:00.000', 'out': global_out},
    )
    _prop(sequence, 'kdenlive:uuid', f'{{{seq_uuid}}}')
    _prop(sequence, 'kdenlive:clipname', 'Sequence 1')
    ET.SubElement(sequence, 'track', producer='producer0')
    for track_id in sequence_tracks:
        ET.SubElement(sequence, 'track', producer=track_id)

    _prop(playlist_bin, 'kdenlive:docproperties.uuid', f'{{{seq_uuid}}}')
    _prop(playlist_bin, 'kdenlive:docproperties.version', '1.1')
    _prop(playlist_bin, 'xml_retain', '1')
    ET.SubElement(
        playlist_bin,
        'entry',
        attrib={'producer': f'{{{seq_uuid}}}', 'in': '00:00:00.000', 'out': '00:00:00.000'},
    )
    for element_id in bin_element_ids:
        ET.SubElement(
            playlist_bin, 'entry', attrib={'producer': element_id, 'in': '00:00:00.000'}
        )

    final_tractor = ET.SubElement(
        mlt,
        'tractor',
        attrib={'id': 'tractorfinal', 'in': '00:00:00.000', 'out': global_out},
    )
    _prop(final_tractor, 'kdenlive:projectTractor', '1')
    ET.SubElement(
        final_tractor,
        'track',
        attrib={'producer': f'{{{seq_uuid}}}', 'in': '00:00:00.000', 'out': global_out},
    )

    tree = ET.ElementTree(mlt)
    ET.indent(tree, space='\t', level=0)
    tree.write(output_path, xml_declaration=True, encoding='utf-8')

    return output_path
