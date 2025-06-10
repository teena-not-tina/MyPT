# utils/data_converter.py - 데이터 변환 유틸리티

def convert_v3_to_current_format(v3_data):
    """V3 데이터를 현재 형식으로 변환"""
    if not v3_data:
        return []
    
    converted_ingredients = []
    
    for idx, item in enumerate(v3_data):
        if isinstance(item, str):
            converted_ingredients.append({
                "id": idx + 1,
                "name": item,
                "quantity": 1,
                "confidence": 0.7,
                "source": "v3_text_migration"
            })
        elif isinstance(item, dict):
            name = (item.get("name") or 
                   item.get("ingredient") or 
                   item.get("food") or 
                   item.get("foodName") or 
                   "Unknown ingredient")
            
            quantity = (item.get("quantity") or 
                       item.get("count") or 
                       item.get("amount") or 1)
            
            converted_ingredients.append({
                "id": item.get("id", idx + 1),
                "name": name,
                "quantity": max(1, int(quantity)),
                "confidence": item.get("confidence", 0.5),
                "source": item.get("source", "v3_migration")
            })
    
    return converted_ingredients