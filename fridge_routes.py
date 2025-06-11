# fridge_routes.py - 냉장고 데이터 관련 라우터들

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import traceback
from config.database import DB_NAME, COLLECTION_NAME

fridge_router = APIRouter()

class Ingredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: Optional[float] = 0.8
    source: str = "analysis"
    bbox: Optional[List[float]] = None
    originalClass: Optional[str] = None
    ensemble_info: Optional[Dict] = None

    class Config:
        from_attributes = True

class FridgeData(BaseModel):
    userId: str
    ingredients: List[Ingredient]
    timestamp: str
    totalCount: int
    totalTypes: int
    analysisMethod: Optional[str] = "ensemble"
    deviceInfo: Optional[str] = None

    class Config:
        from_attributes = True

class SimpleIngredient(BaseModel):
    id: int
    name: str
    quantity: int
    confidence: float
    source: str

class SimpleFridgeData(BaseModel):
    userId: str
    ingredients: List[SimpleIngredient]

@fridge_router.post("/api/fridge/save")
async def save_fridge_data(fridge_data: FridgeData):
    from main import fridge_collection, client
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")

    try:
        print(f"\n=== Fridge Save API Called ===")
        print(f"User: {fridge_data.userId}")
        print(f"Ingredients: {fridge_data.totalTypes} types, {fridge_data.totalCount} items")

        ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]

        try:
            await client.admin.command('ping')
            print("MongoDB connection OK")
        except Exception as conn_err:
            print(f"MongoDB connection check failed: {conn_err}")
            raise HTTPException(status_code=503, detail="MongoDB connection unstable")

        current_time = datetime.now().isoformat()

        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "timestamp": fridge_data.timestamp,
            "totalCount": fridge_data.totalCount,
            "totalTypes": fridge_data.totalTypes,
            "analysisMethod": fridge_data.analysisMethod or "ensemble",
            "deviceInfo": fridge_data.deviceInfo or "web_app",
            "updatedAt": current_time
        }

        insert_only_document = {
            "createdAt": current_time
        }

        result = await fridge_collection.update_one(
            {"userId": fridge_data.userId},
            {
                "$set": update_document,
                "$setOnInsert": insert_only_document
            },
            upsert=True
        )

        print(f"Save complete. New document: {result.upserted_id is not None}")

        return {
            "success": True,
            "message": f"Fridge data successfully saved to {DB_NAME}.{COLLECTION_NAME}",
            "userId": fridge_data.userId,
            "totalTypes": fridge_data.totalTypes,
            "totalCount": fridge_data.totalCount,
            "isNew": result.upserted_id is not None,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "documentId": str(result.upserted_id) if result.upserted_id else "updated"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in save_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")

@fridge_router.post("/api/fridge/save-simple")
async def save_simple_fridge_data(fridge_data: SimpleFridgeData):
    from main import fridge_collection, client
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")

    try:
        print(f"\n=== Simple Fridge Save API Called ===")
        print(f"User: {fridge_data.userId}")
        print(f"Ingredients: {len(fridge_data.ingredients)}")

        ingredients_dict = [ingredient.model_dump() for ingredient in fridge_data.ingredients]

        try:
            await client.admin.command('ping')
            print("MongoDB connection OK")
        except Exception as conn_err:
            print(f"MongoDB connection check failed: {conn_err}")
            raise HTTPException(status_code=503, detail="MongoDB connection unstable")

        current_time = datetime.now().isoformat()

        insert_only_document = {
            "createdAt": current_time
        }

        update_document = {
            "userId": fridge_data.userId,
            "ingredients": ingredients_dict,
            "updatedAt": current_time
        }

        result = await fridge_collection.update_one(
            {"userId": fridge_data.userId},
            {
                "$set": update_document,
                "$setOnInsert": insert_only_document
            },
            upsert=True
        )

        print(f"Simple save complete. New document: {result.upserted_id is not None}")

        return {
            "success": True,
            "message": f"Simplified fridge data successfully saved to {DB_NAME}.{COLLECTION_NAME}",
            "userId": fridge_data.userId,
            "totalIngredients": len(fridge_data.ingredients),
            "isNew": result.upserted_id is not None,
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME,
                "documentId": str(result.upserted_id) if result.upserted_id else "updated",
                "format": "simplified"
            },
            "savedFields": ["userId", "ingredients", "createdAt"]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR in save_simple_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Simplified save error: {str(e)}")

@fridge_router.get("/api/fridge/load/{user_id}")
async def load_fridge_data(user_id: str):
    from main import fridge_collection
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")

    try:
        print(f"\n=== Fridge Load API Called ===")
        print(f"User: {user_id}")

        fridge_data = await fridge_collection.find_one({"userId": user_id})

        if not fridge_data:
            print(f"No data found for user: {user_id}")
            return {
                "success": False,
                "message": "No saved fridge data found",
                "ingredients": [],
                "totalTypes": 0,
                "totalCount": 0,
                "storage": {
                    "database": DB_NAME,
                    "collection": COLLECTION_NAME
                }
            }

        fridge_data.pop("_id", None)

        print(f"Data loaded successfully")

        return {
            "success": True,
            "message": f"Data successfully loaded from {DB_NAME}.{COLLECTION_NAME}",
            "storage": {
                "database": DB_NAME,
                "collection": COLLECTION_NAME
            },
            **fridge_data
        }

    except Exception as e:
        print(f"\nERROR in load_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Load error: {str(e)}")

@fridge_router.get("/api/fridge/load-simple/{user_id}")
async def load_simple_fridge_data(user_id: str):
    from main import fridge_collection
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")

    try:
        print(f"\n=== Simple Fridge Load API Called ===")
        print(f"User: {user_id}")

        fridge_data = await fridge_collection.find_one({"userId": user_id})

        if not fridge_data:
            print(f"No data found for user: {user_id}")
            return {
                "success": False,
                "message": "No saved fridge data found",
                "ingredients": []
            }

        fridge_data.pop("_id", None)

        simplified_data = {
            "userId": fridge_data.get("userId"),
            "ingredients": fridge_data.get("ingredients", []),
            "createdAt": fridge_data.get("createdAt")
        }

        print(f"Simple data loaded successfully")

        return {
            "success": True,
            "message": f"Simplified data successfully loaded from {DB_NAME}.{COLLECTION_NAME}",
            **simplified_data
        }

    except Exception as e:
        print(f"\nERROR in load_simple_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Simplified load error: {str(e)}")

@fridge_router.get("/api/fridge/load-v3/{user_id}")
async def load_v3_fridge_data(user_id: str):
    from main import fridge_collection, db
    from utils.data_converter import convert_v3_to_current_format

    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")

    try:
        print(f"\n=== V3 Fridge Load API Called ===")
        print(f"User: {user_id}")

        v3_collections = [
            f"{COLLECTION_NAME}_v3",
            f"{COLLECTION_NAME}_old", 
            "fridge_v3",
            "ingredients_v3",
            "food_data_v3"
        ]

        v3_data = None
        found_collection = None

        for collection_name in v3_collections:
            try:
                v3_collection = db[collection_name]
                data = await v3_collection.find_one({"userId": user_id})
                if data:
                    v3_data = data
                    found_collection = collection_name
                    break
            except Exception as e:
                print(f"Collection {collection_name} search failed: {e}")
                continue

        if not v3_data:
            current_data = await fridge_collection.find_one({"userId": user_id})
            if current_data:
                if "ingredients" in current_data and isinstance(current_data["ingredients"], list):
                    if current_data["ingredients"]:
                        print(f"Found data in current collection")
                        return {
                            "success": True,
                            "data": current_data["ingredients"],
                            "source": "current_format",
                            "collection": COLLECTION_NAME,
                            "message": "Returned current format data"
                        }

                v3_data = current_data
                found_collection = COLLECTION_NAME

        if not v3_data:
            return {
                "success": False,
                "message": "No v3 or previous format data found",
                "searched_collections": v3_collections + [COLLECTION_NAME]
            }

        v3_ingredients = None

        for field_name in ["ingredients", "data", "items", "foods", "detected_items"]:
            if field_name in v3_data and v3_data[field_name]:
                v3_ingredients = v3_data[field_name]
                break

        if not v3_ingredients:
            return {
                "success": False,
                "message": "No ingredient data found in v3 data",
                "available_fields": list(v3_data.keys()),
                "source_collection": found_collection
            }

        converted_data = convert_v3_to_current_format(v3_ingredients)

        print(f"V3 data conversion complete")
        print(f"  Original: {len(v3_ingredients)} items")
        print(f"  Converted: {len(converted_data)} items") 
        print(f"  Source: {found_collection}")

        return {
            "success": True,
            "data": converted_data,
            "source": "v3_migration",
            "collection": found_collection,
            "original_count": len(v3_ingredients),
            "converted_count": len(converted_data),
            "message": f"V3 data successfully converted ({found_collection})"
        }

    except Exception as e:
        print(f"\nERROR in load_v3_fridge_data:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"V3 data load error: {str(e)}")

@fridge_router.post("/api/fridge/migrate-v3/{user_id}")
async def migrate_v3_to_current(user_id: str):
    from main import fridge_collection
    if fridge_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not connected")

    try:
        print(f"\n=== V3 Migration API Called ===")
        print(f"User: {user_id}")

        v3_response = await load_v3_fridge_data(user_id)

        if not v3_response["success"]:
            return {
                "success": False,
                "message": "No v3 data to migrate",
                "details": v3_response
            }

        converted_data = v3_response["data"]

        current_time = datetime.now().isoformat()

        migration_document = {
            "userId": user_id,
            "ingredients": converted_data,
            "timestamp": current_time,
            "totalCount": sum(item["quantity"] for item in converted_data),
            "totalTypes": len(converted_data),
            "analysisMethod": "v3_migration",
            "deviceInfo": "migration_tool",
            "migrationInfo": {
                "sourceCollection": v3_response["collection"],
                "migrationDate": current_time,
                "originalCount": v3_response["original_count"],
                "convertedCount": v3_response["converted_count"]
            },
            "updatedAt": current_time,
            "createdAt": current_time
        }

        result = await fridge_collection.replace_one(
            {"userId": user_id},
            migration_document,
            upsert=True
        )

        print(f"V3 migration complete")
        print(f"  Converted items: {len(converted_data)}")
        print(f"  Save location: {DB_NAME}.{COLLECTION_NAME}")

        return {
            "success": True,
            "message": "V3 data successfully migrated to current format",
            "migrationInfo": {
                "userId": user_id,
                "sourceCollection": v3_response["collection"],
                "migratedItems": len(converted_data),
                "totalCount": migration_document["totalCount"],
                "totalTypes": migration_document["totalTypes"],
                "targetCollection": f"{DB_NAME}.{COLLECTION_NAME}",
                "migrationDate": current_time
            }
        }

    except Exception as e:
        print(f"\nERROR in migrate_v3_to_current:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")