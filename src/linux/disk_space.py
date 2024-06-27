import subprocess
import os
from typing import Tuple

from utils.custom_logger import logger

def get_previous_disk_space() -> Tuple[int, int]:
    """Retrieves the previous disk space values from a file."""
    try:
        with open("previous_disk_space.txt", "r") as file:
            available, total = file.read().split(',')
            return int(available), int(total)
    except FileNotFoundError:
        return 0, 0  # Return 0,0 if the file does not exist

def update_previous_disk_space(available_space_gb: int, total_space_gb: int):
    """Updates the file with the current disk space values."""
    with open("previous_disk_space.txt", "w") as file:
        file.write(f"{available_space_gb},{total_space_gb}")

def run_df_command() -> str:
    """Runs the df command and returns its output."""
    try:
        result = subprocess.run(['df', '-BG'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running df command: {e}") from e

def parse_df_output(df_output: str, target_partition: str) -> Tuple[str, str]:
    """Parses the df command output and extracts disk space information for the target partition."""
    lines = df_output.splitlines()
    if len(lines) < 2:
        raise ValueError("Unexpected output format from df command")
    
    def extract_disk_space_info(lines, target_partition):
        for line in lines[1:]:
            parts = line.split()
            if parts[0] == target_partition:
                headers = lines[0].split()
                values = line.split()
                available_space_index = headers.index("Available") if "Available" in headers else headers.index("Avail")
                total_space_index = headers.index("1G-blocks") if "1G-blocks" in headers else headers.index("Size")
                available_space_gb = values[available_space_index].rstrip('G')
                total_space_gb = values[total_space_index].rstrip('G')
                return available_space_gb, total_space_gb
    
    # Call the extracted function
    _, _ = extract_disk_space_info(lines, target_partition)
    raise ValueError(f"No data found for {target_partition}")

def log_and_format_disk_space(available_space_gb: str, total_space_gb: str) -> str:
    """Logs and formats the disk space information."""
    logger.info(f"Available space: {available_space_gb} GB, Total space: {total_space_gb} GB")
    return f"{available_space_gb}GB / {total_space_gb}GB"

def get_disk_space() -> str:
    target_partition = '/dev/sdb'
    try:
        df_output = run_df_command()
        available_space_gb, total_space_gb = parse_df_output(df_output, target_partition)
        
        prev_available, _ = get_previous_disk_space()
        current_available = int(available_space_gb)
        
        # Determine the arrow symbol
        if current_available > prev_available:
            arrow = "↑"
        elif current_available < prev_available:
            arrow = "↓"
        else:
            arrow = ""
        
        # Update the previous disk space for next comparison
        update_previous_disk_space(current_available, int(total_space_gb))
        
        return log_and_format_disk_space(f"{available_space_gb}{arrow}", total_space_gb)
    except (RuntimeError, ValueError) as e:
        return str(e)