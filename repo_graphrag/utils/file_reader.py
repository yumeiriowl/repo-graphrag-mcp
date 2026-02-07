import os
import logging
from typing import Dict, Tuple
from ..config.settings import (
    doc_ext_dict, 
    code_ext_dict, 
    no_process_file_list
)


logger = logging.getLogger(__name__)

def read_dir(read_dir_path: str) -> Tuple[Dict[str, str], Dict[str, bytes]]:
    """
    Traverse a directory and collect files to process.

    Args:
        read_dir_path: Target directory path to read

    Returns:
        tuple: (doc_dict, code_dict) - Dictionaries for document files and code files
        - doc_dict: file_path → text content
        - code_dict: file_path → bytes content
    """
    logger.info("=" * 50)
    logger.info("Planned files to process")
    logger.info(f"Exclude list: {no_process_file_list}")

    doc_dict = {}
    code_dict = {}

    # Build the set of allowed extensions (documents + code)
    allow_ext_set = set(doc_ext_dict["text_file"]) | set(code_ext_dict.keys())
    # Special files without extensions to include
    special_files = set(doc_ext_dict.get("special_files", []))

    # Recursively traverse the directory
    for dir_path, dir_names, file_name_list in os.walk(read_dir_path):
        # Exclude directories in the no-process list
        for no_process in no_process_file_list:
            if no_process in dir_names:
                dir_names.remove(no_process)
                logger.info(f"Excluded directory: {os.path.join(dir_path, no_process)}")
                
        for file_name in file_name_list:
            # Skip files in the no-process list
            if file_name in no_process_file_list:
                logger.info(f"Excluded file: {os.path.join(dir_path, file_name)}")
                continue

            # Extract extension
            _, ext = os.path.splitext(file_name)
            ext_without_dot = ext.lstrip(".")
            
            # Lowercase filename to check special files
            file_name_lower = file_name.lower()
            is_special_file = file_name_lower in special_files

            # Skip files that are neither allowed extension nor special files
            if ext_without_dot not in allow_ext_set and not is_special_file:
                continue

            # Build absolute file path
            file_path = os.path.join(dir_path, file_name)

            # Read file content into dictionaries
            if ext_without_dot in code_ext_dict:
                with open(file_path, "rb") as file:
                    content = file.read()
                if content.strip():
                    code_dict[file_path] = content
                    logger.info(f"Code file: {file_path}")
                else:
                    logger.info(f"Skipping empty code file: {file_path}")
                    continue
            elif ext_without_dot in doc_ext_dict["text_file"] or is_special_file:
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        doc_dict[file_path] = file.read()
                    logger.info(f"Text file: {file_path}")
                except UnicodeDecodeError:
                    # Try alternative encodings when UTF-8 fails
                    try:
                        with open(file_path, "r", encoding="shift_jis") as file:
                            doc_dict[file_path] = file.read()
                        logger.info(f"Text file (Shift_JIS): {file_path}")
                    except UnicodeDecodeError:
                        logger.warning(f"Skipping due to encoding error: {file_path}")

    logger.info("=" * 50 + "\n")

    return doc_dict, code_dict
