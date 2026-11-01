from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
client = None
db = None
collection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, collection
    #I don't care you can have my key
    uri = "mongodb+srv://User:TLJKtUDr5OlSWmnd@cluster0.xsgbujs.mongodb.net/"
    client = AsyncIOMotorClient(uri)
    db = client['ev_db']
    collection = db['vehicles']
    print("connected")
    yield
    client.close()
    print("connection closed")
app = FastAPI(lifespan=lifespan)

@app.post("/insert-fast")
async def insert_fast(payload: dict):
    try:
        concerns = collection.with_options(
            write_concern = WriteConcern(w=1, j=True, wtimeout=5000)
        )
        result=await concerns.insert_one(payload)
        return str(result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insert-safe")
async def insert_safe(payload: dict):
    try:
        concerns = collection.with_options(
            write_concern = WriteConcern(w="majority", j=True, wtimeout=5000)
        )
        result=await concerns.insert_one(payload)
        return str(result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/count-tesla-primary")
async def count_tesla_primary():
    try:
        concerns = collection.with_options(
            read_preference = ReadPreference.PRIMARY
        )
        result = await concerns.aggregate([
                {"$match":{"Make":"TESLA"}},
                {"$count": "count"}
            ]).to_list(length=1)
        count = result[0]["count"] if result else 0
        return {"count":count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/count-bmw-secondary")
async def count_bmw_secondary():
    try:
        concerns = collection.with_options(
            read_preference = ReadPreference.SECONDARY
        )
        try:
            result = await concerns.aggregate([
                    {"$match":{"Make":"BMW"}},
                    {"$count": "count"}
                ]).to_list(length=1)
        except Exception:
            concerns = collection.with_options(
                read_preference = ReadPreference.PRIMARY
            )
            result = await concerns.aggregate([
                    {"$match":{"Make":"BMW"}},
                    {"$count": "count"}
                ]).to_list(length=1)
            
        count = result[0]["count"] if result else 0
        return {"count":count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
