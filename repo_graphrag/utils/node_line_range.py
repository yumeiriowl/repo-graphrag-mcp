import bisect
import logging
from typing import List, Tuple
from tree_sitter import Node

logger = logging.getLogger(__name__)

def get_node_line_range(node: Node, line_offset_list: List[int]) -> Tuple[int, int]:
    """
    Get the line-range spanned by a syntax node.

    Args:
        node: A Tree-sitter node
        line_offset_list: List of byte offsets for the start of each line

    Returns:
        Tuple[int, int]: (start_line, end_line)
    """
    # Get byte span from node
    start_byte = node.start_byte
    end_byte = node.end_byte

    # Convert byte positions to line indices
    start_line = bisect.bisect_right(line_offset_list, start_byte) - 1
    end_line = bisect.bisect_right(line_offset_list, end_byte) - 1

    # Return 1-based line numbers
    return start_line + 1, end_line + 1
