from .stream import PipeStreamHandler
from datetime import datetime
from helper.ctxtools import ctx
import re

REG_SIZE = re.compile(r'(\d+)([a-zA-Z]+)')
REG_COPYRIGHT = re.compile(
    r"ffmpeg\s+version\s+(.*?)\s+Copyright\s+\(\w+\)\s+\d+-\d+\s+the\s+FFmpeg\s+\w+\s*"
)
REG_INPUT = re.compile(
    r"Input\s+#(\d+),\s+((?:\w+,)+)\s+from\s+'(.*?)':"
)
REG_METADATA = re.compile(
    r"Metadata:\s*\n((\s{4}(\w+)\s*:\s*\s(.*?)\n)+)"
)
REG_INPUT_EXTRA = re.compile(
    r"Duration:\s*([\d:\.]+)\s*, start:\s*([\w\.]+),\s*bitrate:\s*(.*?)\n"
)
REG_INPUT_STREAM = re.compile(
    r"Duration:\s*([\d:\.]+)\s*, start:\s*([\w\.]+),\s*bitrate:\s*(.*?)\n((?:\s{4}Stream\s*#(?:\d+):\d+(?:\(\w+\))?:\s*(?:.*?)\n(?:\s*Metadata:\s*\n(?:(?:\s{6}(?:\w+)\s*:\s*\s(?:.*?)\n)+))?)*)"
)
REG_OUTPUT = re.compile(
    r"Output\s+#(\d+),\s+((?:\w+,)+)\s+to\s+'(.*?'):"
)
REG_STREAM = re.compile(
    r"Stream\s*#(\d+):(\d+)(?:\(\w+\))?:\s*(.*?)\n(\s*Metadata:\s*\n(\s{6}(\w+)\s*:\s*\s(.*?)\n)+)?"
)
REG_STREAM_MAPPING = re.compile(
    r'Stream\s+mapping:'
)
REG_FRAME = re.compile(
    r'frame=\s*(.*?)\s*fps=\s*(.*?)\s*q=\s*(.*?)\s*L?size=\s*(.*?)\s*time=\s*(.*?)\s*bitrate=\s*(.*?)\s*speed=\s*(.*?)\s'
)
REG_FRAME_END = re.compile(
    r"video:\s*(\w+)\s+audio:\s*(\w+)\s+subtitle:\s*(\w+)\s+other streams:\s*(\w+)\s+global headers:\s*(\w+)\s+muxing overhead:\s*([\w\.%]+)"
)

CHECKPOINT_SEQUENCES = [
    lambda _, line: bool(REG_COPYRIGHT.match(line)),
    lambda _, line: bool(REG_INPUT.match(line)),
    lambda _, line: bool(REG_OUTPUT.match(line)),
    # lambda _, line: bool(REG_STREAM_MAPPING.match(line)),
    # lambda _, line: bool(REG_FRAME_START.match(line)),
    lambda _, line: bool(REG_FRAME.match(line)),
    lambda _, line: bool(REG_FRAME_END.match(line)),
]

CHECKPOINT_COPYRIGHT = 0
CHECKPOINT_INPUT = 1
CHECKPOINT_OUTPUT = 2
# CHECKPOINT_MAPPING = 3
# CHECKPOINT_FRAME = 4
# CHECKPOINT_RESULT = 5
CHECKPOINT_FRAME = 3
CHECKPOINT_RESULT = 4


def split_colon_keyword_dict(s):
    retdict = {}
    for line in [i.strip() for i in s.split('\n') if i]:
        k, v = line.split(':', 1)
        k, v = k.strip(), v.strip()
        retdict[k] = v
    return retdict


class FfmpegStreamHandler(PipeStreamHandler):
    def __init__(self, process):
        super().__init__(process)
        self.output_sequences = []
        self.cp_iter = iter(CHECKPOINT_SEQUENCES)

        self.checkpoint = next(self.cp_iter)

    def stop_threadsafe(self):
        return self.feed_threadsafe(b'q').result()

    async def stop(self):
        return await self.feed_data(b'q')

    def _get_frame(self):
        try:
            frame = self.output_sequences[CHECKPOINT_FRAME][-1]
        except IndexError:
            return {}
        else:
            (
                frame,
                fps,
                q,
                size,
                time,
                bitrate,
                speed,
             ) = REG_FRAME.search(frame).groups()
            return {
                'frame': frame,
                'fps': fps,
                'q': q,
                'size': size,
                'bitrate': bitrate,
                'speed': speed,
                'time': time,
            }

    @staticmethod
    def _file_metadata(metadata_str):
        metadata = REG_METADATA.search(metadata_str)
        metadata_dict = {}
        if metadata:
            filed, *_ = metadata.groups()
            metadata_dict = split_colon_keyword_dict(filed)
        return metadata_dict

    def get_inputs(self):
        try:
            input_str = ''.join(
                self.output_sequences[CHECKPOINT_INPUT])
        except IndexError:
            return {}
        else:
            # 输入节点分割
            _, *valid_seq = REG_INPUT.split(input_str)
            input_lst = []
            for i in range(0, len(valid_seq), 4):
                index, formats, path, data = valid_seq[i: i+4]
                formats = [i for i in formats.split(',') if i]

                # input metadata
                metadata_dict = self._file_metadata(data)

                # input stream
                input_streams_result = REG_INPUT_STREAM.findall(data)
                input_stream_lst = []
                if input_streams_result:
                    for stream_result in input_streams_result:
                        (
                            duration,
                            start,
                            bitrate,
                            stream_str
                        ) = stream_result
                        streams = []
                        for s in REG_STREAM.findall(stream_str):
                            (
                                stream_id,
                                stream_index,
                                stream_desc,
                                stream_metas,
                                *_
                            ) = s
                            streams.append({
                                'id': stream_id,
                                'index': stream_index,
                                'description': stream_desc.strip(),
                                'metadata': split_colon_keyword_dict(stream_metas),
                                'type': stream_desc.strip().split(':', 1)[0].lower(),
                            })

                        input_stream_lst.append({
                            'duration': duration,
                            'start': start,
                            'bitrate': bitrate.strip(),
                            'streams': streams
                        })

                input_lst.append({
                    'id': index,
                    'formats': formats,
                    'metadata': metadata_dict,
                    'streams': input_stream_lst
                })

            return input_lst

    def get_outputs(self):
        try:
            output_str = ''.join(self.output_sequences[CHECKPOINT_OUTPUT])
        except IndexError:
            return {}
        else:
            # 输出节点分割
            _, *valid_seq = REG_OUTPUT.split(output_str)
            output_lst = []
            for i in range(0, len(valid_seq), 4):
                index, formats, path, data = valid_seq[i: i + 4]
                formats = [i for i in formats.split(',') if i]

                # output metadata
                metadata_dict = self._file_metadata(data)

                # output stream
                output_streams_result = REG_STREAM.findall(data)
                output_stream_lst = []
                if output_streams_result:
                    for stream_result in output_streams_result:
                        (
                            stream_id,
                            stream_index,
                            stream_desc,
                            stream_metas,
                            *_
                        ) = stream_result
                        output_stream_lst.append({
                            'id': stream_id,
                            'index': stream_index,
                            'description': stream_desc.strip(),
                            'metadata': split_colon_keyword_dict(stream_metas),
                        })

                output_lst.append({
                    'id': index,
                    'formats': formats,
                    'metadata': metadata_dict,
                    'streams': output_stream_lst
                })

            return output_lst

    def speed(self):
        frame_dict = self._get_frame()
        return frame_dict.get('speed', 'unknown')

    def size(self):
        frame_dict = self._get_frame()
        return frame_dict.get('size', 0)

    def complete_length(self):
        frame_dict = self._get_frame()
        tm = datetime.strptime(
            frame_dict.get('time', '00:00:00.00'),
            '%H:%M:%S.%f'
        )
        time_length = (
            tm.hour * 3600 +
            tm.minute * 60 +
            tm.second +
            tm.microsecond / 1e6
        )
        return time_length

    def total_length(self):
        self.get_inputs()
        return 0

    def complete_percent(self):
        return self.complete_length() / self.total_length()

    def bitrate(self):
        frame_dict = self._get_frame()
        return frame_dict.get('bitrate', 'unknown')

    def fps(self):
        frame_dict = self._get_frame()
        return frame_dict.get('fps', 'unknown')

    async def _stream_handler(self, stream_id, line):
        if self.checkpoint(stream_id, line):
            self.output_sequences.append([])
            try:
                self.checkpoint = next(self.cp_iter)
            except StopIteration:
                # 剩余的不在checkpoint中的输出都保存在最后一个列表
                self.checkpoint = lambda *_: False
        self.output_sequences[-1].append(line)
        return True


if __name__ == '__main__':
    print()