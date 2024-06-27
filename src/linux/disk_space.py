import subprocess

def get_disk_space() -> str:
    target_partition = '/dev/sdb'
    
    try:
        result = subprocess.run(['df', '-BG'], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return f"Error running df command: {e}"
    
    lines = result.stdout.splitlines()
    if len(lines) < 2:
        return "Unexpected output format from df command"
    
    for line in lines[1:]:
        parts = line.split()
        if parts[0] == target_partition:
            headers = lines[0].split()
            values = line.split()
            if "Available" in headers and "1G-blocks" in headers:
                available_space_index = headers.index("Available")
                total_space_index = headers.index("1G-blocks")
            elif "Avail" in headers and "Size" in headers:  # Some versions of 'df' abbreviate 'Available' as 'Avail'
                available_space_index = headers.index("Avail")
                total_space_index = headers.index("Size")
            else:
                return "Could not find space information in df output"
            
            available_space_gb = values[available_space_index].rstrip('G')
            total_space_gb = values[total_space_index].rstrip('G')
            return f"{available_space_gb} GB / {total_space_gb} GB"
    
    return f"No data found for {target_partition}"