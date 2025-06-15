"""
Path utilities for safe file access across all scripts.
This module should be imported by all scripts that need to access datasets or create outputs.
"""

import os
import sys
import json
import pandas as pd

def load_path_config():
    """Load path configuration from JSON file"""
    # Look for config in parent directory (project root)
    config_path = os.path.join('..', 'path_config.json')
    if not os.path.exists(config_path):
        config_path = 'path_config.json'  # Try current directory
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            "Path configuration not found. Please run master.py first to generate path_config.json"
        )
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def get_dataset_path(dataset_key):
    """Get validated dataset file path"""
    config = load_path_config()
    
    if dataset_key not in config['datasets']:
        available = list(config['datasets'].keys())
        raise ValueError(f"Dataset key '{dataset_key}' not found. Available: {available}")
        
    return config['datasets'][dataset_key]

def safe_read_csv(dataset_key, max_rows=100000, **pandas_kwargs):
    """Safely read CSV with validation and security checks"""
    filepath = get_dataset_path(dataset_key)
    
    # Check file size (limit to 50MB)
    file_size = os.path.getsize(filepath)
    if file_size > 50 * 1024 * 1024:
        raise ValueError(f"Dataset file too large: {file_size / (1024*1024):.1f}MB (limit: 50MB)")
    
    # Read with row limit
    df = pd.read_csv(filepath, nrows=max_rows, **pandas_kwargs)
    
    # Sanitize data to prevent formula injection
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).apply(
            lambda x: x if not str(x).startswith(('=', '+', '-', '@')) else f"'{x}"
        )
    
    print(f"✓ Loaded {len(df)} rows from {dataset_key}")
    return df

def get_output_path(directory_key, filename):
    """Get validated output path for saving files"""
    config = load_path_config()
    
    if directory_key not in config['directories']:
        available = list(config['directories'].keys())
        raise ValueError(f"Directory key '{directory_key}' not allowed. Available: {available}")
        
    output_dir = config['directories'][directory_key]
    
    # Sanitize filename
    safe_filename = _sanitize_filename(filename)
    
    # Create directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, safe_filename)
    
    # Security check
    abs_output_path = os.path.abspath(output_path)
    abs_output_dir = os.path.abspath(output_dir)
    if not abs_output_path.startswith(abs_output_dir):
        raise ValueError("Security violation: output path outside intended directory")
        
    return abs_output_path

def _sanitize_filename(filename):
    """Sanitize filename to prevent security issues"""
    import re
    # Remove/replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove path traversal attempts
    sanitized = sanitized.replace('..', '_').replace('~', '_')
    # Limit length
    sanitized = sanitized[:255]
    # Ensure it's not empty or dangerous
    if not sanitized or sanitized in ['.', '..']:
        sanitized = 'unnamed_file'
    return sanitized

# Dataset key constants for easy reference
DATASET_KEYS = {
    'INSTAGRAM_ANALYTICS_EXCEL': 'instagram_analytics_excel',
    'INSTAGRAM_AGE_GENDER': 'instagram_age_gender', 
    'INSTAGRAM_POST_ENGAGEMENT': 'instagram_post_engagement',
    'INSTAGRAM_PROFILE_OVERVIEW': 'instagram_profile_overview',
    'INSTAGRAM_TOP_CITIES': 'instagram_top_cities'
}

# Directory key constants
DIRECTORY_KEYS = {
    'GRAPHS': 'graphs',
    'LOG': 'log',
    'DATASET': 'dataset'
}