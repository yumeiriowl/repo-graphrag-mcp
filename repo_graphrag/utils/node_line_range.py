import bisect
import logging
from typing import List, Tuple
from tree_sitter import Node

logger = logging.getLogger(__name__)

def build_line_offset_list(file_content_bytes: bytes) -> List[int]:
    """Build a list of byte offsets for the start of each line.

    Args:
        file_content_bytes: Raw file content

    Returns:
        List[int]: Byte offsets
    """
    offsets: List[int] = [0]
    for i, b in enumerate(file_content_bytes):
        if b == 0x0A:
            if i + 1 < len(file_content_bytes):
                offsets.append(i + 1)
    return offsets


def get_node_line_range(node: Node, line_offset_list: List[int]) -> Tuple[int, int]:
    """Get 1-based (start_line, end_line) for a Tree-sitter node.

    Args:
        node: Tree-sitter node
        line_offset_list: List of byte offsets for line starts
    """
    start_byte = node.start_byte
    end_byte_exclusive = node.end_byte

    start_line_idx = bisect.bisect_right(line_offset_list, start_byte) - 1

    end_lookup_byte = end_byte_exclusive - 1 if end_byte_exclusive > 0 else 0
    end_line_idx = bisect.bisect_right(line_offset_list, end_lookup_byte) - 1

    return start_line_idx + 1, end_line_idx + 1
