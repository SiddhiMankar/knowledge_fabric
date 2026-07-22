import os
import json

def load_chunks(filepath='data/processed/chunks.json'):
    """Loads and returns the processed document chunks from the specified JSON file."""
    if not os.path.exists(filepath):
        print(f"Warning: Chunk file not found at {filepath}")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading chunks from {filepath}: {e}")
        return []
