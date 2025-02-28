"""Docker utility functions."""

def get_volume_name(container_name):
    """Get volume name from container name by replacing container with volume.
    
    Args:
        container_name: Name of the container
        
    Returns:
        str: Name of the volume
    """
    return container_name.replace("container", "volume")

def generate_container_name(prefix="edge_node_container_"):
    """Generate a unique container name.
    
    Args:
        prefix: Prefix for the container name
        
    Returns:
        str: Unique container name
    """
    import random
    import string
    
    # Generate a random 6-character suffix
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    return f"{prefix}{suffix}" 