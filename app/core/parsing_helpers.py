import re

def normalize_key(key: str) -> str:
    """Normalizes a string for matching by lowercasing, removing accents, and simplifying."""
    if not isinstance(key, str):
        return ""
    s = key.lower()
    s = s.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    s = s.replace('à', 'a').replace('â', 'a')
    s = s.replace('ç', 'c')
    s = re.sub(r'[^a-z0-9\s_]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def find_field_value(row: dict, possible_fields: list, exclude_fields: list = []) -> str or None:
    """
    Finds a value in a dictionary by checking against a list of possible keys,
    including partial and "starts with" matches.
    """
    if not row:
        return None
    
    normalized_row = {normalize_key(k): v for k, v in row.items() if v is not None and str(v).strip() != ''}
    normalized_exclude = [normalize_key(f) for f in exclude_fields]
    
    available_keys = list(normalized_row.keys())
    
    for field in possible_fields:
        normalized_field = normalize_key(field)
        
        # 1. Check for an exact match first
        if normalized_field in normalized_row and normalized_field not in normalized_exclude:
            return str(normalized_row[normalized_field])
            
        # 2. Check for keys that START WITH the desired field name
        # This will match "numero appele a1 f1" when looking for "numero appele"
        for key in available_keys:
            if key.startswith(normalized_field) and key not in normalized_exclude:
                return str(normalized_row[key])
                    
    return None