"""
Subprocess Global Hook

This module patches the standard subprocess module to hide all console windows
by default on Windows systems. Import this module early in your application.
"""

import os
import sys
import subprocess
import functools
import logging

# Setup basic logging if not already configured
logging.basicConfig(level=logging.INFO)

# Store original functions before patching
_orig_popen = subprocess.Popen
_orig_call = subprocess.call
_orig_check_call = subprocess.check_call
_orig_check_output = subprocess.check_output
_orig_run = subprocess.run

def _get_no_window_flags():
    """Get the process creation flags to hide console windows on Windows"""
    if os.name == 'nt':
        # Create startupinfo to hide window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        
        # Return dictionary of kwargs to add
        return {
            'startupinfo': startupinfo,
            'creationflags': subprocess.CREATE_NO_WINDOW
        }
    return {}

def _patch_kwargs(kwargs):
    """Patch kwargs dict with no-window flags if on Windows"""
    if os.name == 'nt':
        try:
            no_window_flags = _get_no_window_flags()
            
            # Only set startupinfo if not already set
            if 'startupinfo' not in kwargs:
                kwargs['startupinfo'] = no_window_flags['startupinfo']
            
            # Add CREATE_NO_WINDOW flag, preserving any existing flags
            flags = kwargs.get('creationflags', 0)
            kwargs['creationflags'] = flags | no_window_flags['creationflags']
        except Exception as e:
            # Log error but continue without modifying kwargs
            logging.warning(f"Failed to patch subprocess kwargs: {e}")
    
    return kwargs

# Patched versions with safe fallbacks
def patched_popen(*args, **kwargs):
    """Patched Popen that hides console windows"""
    try:
        kwargs = _patch_kwargs(kwargs)
        return _orig_popen(*args, **kwargs)
    except Exception as e:
        logging.warning(f"Error in patched_popen, falling back to original: {e}")
        return _orig_popen(*args, **kwargs)

def patched_call(*args, **kwargs):
    """Patched call that hides console windows"""
    try:
        kwargs = _patch_kwargs(kwargs)
        return _orig_call(*args, **kwargs)
    except Exception as e:
        logging.warning(f"Error in patched_call, falling back to original: {e}")
        return _orig_call(*args, **kwargs)

def patched_check_call(*args, **kwargs):
    """Patched check_call that hides console windows"""
    try:
        kwargs = _patch_kwargs(kwargs)
        return _orig_check_call(*args, **kwargs)
    except Exception as e:
        logging.warning(f"Error in patched_check_call, falling back to original: {e}")
        return _orig_check_call(*args, **kwargs)

def patched_check_output(*args, **kwargs):
    """Patched check_output that hides console windows"""
    try:
        kwargs = _patch_kwargs(kwargs)
        return _orig_check_output(*args, **kwargs)
    except Exception as e:
        logging.warning(f"Error in patched_check_output, falling back to original: {e}")
        return _orig_check_output(*args, **kwargs)

def patched_run(*args, **kwargs):
    """Patched run that hides console windows"""
    try:
        kwargs = _patch_kwargs(kwargs)
        return _orig_run(*args, **kwargs)
    except Exception as e:
        logging.warning(f"Error in patched_run, falling back to original: {e}")
        return _orig_run(*args, **kwargs)

def safe_patch_subprocess():
    """Patch all subprocess functions to hide console windows with safety fallbacks"""
    try:
        subprocess.Popen = patched_popen
        subprocess.call = patched_call
        subprocess.check_call = patched_check_call
        subprocess.check_output = patched_check_output
        subprocess.run = patched_run
        logging.info("Subprocess module patched to hide console windows")
        return True
    except Exception as e:
        logging.error(f"Failed to patch subprocess module: {e}")
        return False

# Patched versions of os functions with safe fallbacks
def patched_system(command):
    """Patched os.system that hides console windows on Windows"""
    if os.name == 'nt':
        try:
            # On Windows, use subprocess with hidden window instead of os.system
            patched_kwargs = _patch_kwargs({})
            proc = _orig_popen(command, shell=True, **patched_kwargs)
            return proc.wait()
        except Exception as e:
            logging.warning(f"Error in patched_system, falling back to original: {e}")
            return _orig_system(command)
    else:
        return _orig_system(command)

def patched_popen_os(command, mode='r', buffering=-1):
    """Patched os.popen that hides console windows on Windows"""
    if os.name == 'nt':
        try:
            # Use subprocess.Popen with hidden window
            if 'r' in mode:
                stdout = subprocess.PIPE
                stderr = None
            else:
                stdout = None
                stderr = subprocess.PIPE
                
            patched_kwargs = _patch_kwargs({})
            proc = _orig_popen(command, shell=True, stdout=stdout, stderr=stderr, 
                              text=True, **patched_kwargs)
            
            # Return file-like object that mimics popen behavior
            if 'r' in mode:
                return proc.stdout
            else:
                return proc.stdin
        except Exception as e:
            logging.warning(f"Error in patched_popen_os, falling back to original: {e}")
            return _orig_popen_os(command, mode, buffering)
    else:
        return _orig_popen_os(command, mode, buffering)

def safe_patch_os():
    """Patch os.system and os.popen to hide console windows with safety fallbacks"""
    try:
        _orig_system = os.system
        _orig_popen_os = os.popen
        os.system = patched_system
        os.popen = patched_popen_os
        logging.info("OS module patched to hide console windows")
        return True
    except Exception as e:
        logging.error(f"Failed to patch OS module: {e}")
        return False

# Only apply patches if we're not in a development environment
try:
    # Simple check to see if we're likely in a development environment
    if not any(debugger in sys.modules for debugger in ['pydevd', 'pdb', '_pydev_bundle']):
        safe_patch_subprocess()
        safe_patch_os()
    else:
        logging.info("Development environment detected, skipping subprocess patching")
except Exception as e:
    logging.error(f"Error during subprocess patching setup: {e}") 