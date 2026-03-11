from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.stoner_rock_band
merch_collection = db.merch

# Clear existing merch
merch_collection.delete_many({})

initial_merch = [
    {
        "name": "Cosmic Fog Vinyl",
        "description": "Double LP, 180g blood red vinyl. The complete new album.",
        "price": 35.00,
        "image_url": "https://images.unsplash.com/photo-1538374941097-9e731f4a132e?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60" # Placeholder record player
    },
    {
        "name": "Sabbath Blood T-Shirt",
        "description": "Classic logo on black heavy cotton. True doom style.",
        "price": 25.00,
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60" # Placeholder tshirt
    },
    {
        "name": "Fuzz Pedal Poster",
        "description": "A2 sized poster featuring our iconic fuzz setup.",
        "price": 15.00,
        "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60" # Placeholder concert stage
    },
    {
        "name": "Doom Beanie",
        "description": "Keep warm in the void. Embroidered logo.",
        "price": 20.00,
        "image_url": "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60" # Placeholder beanie
    }
]

merch_collection.insert_many(initial_merch)
print("Seeded database with initial merch.")
