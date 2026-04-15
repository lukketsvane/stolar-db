import json
import os

def create_shards():
    # Load data
    with open('STOLAR/api.json', 'r', encoding='utf-8') as f:
        api_data = json.load(f)
    
    with open('STOLAR/enriched_chairs.json', 'r', encoding='utf-8') as f:
        enriched_data = json.load(f)
    
    image_dir = "STOLAR/bguw"
    
    # Find missing chairs with images
    missing = []
    for chair in api_data.get('chairs', []):
        obj_id = chair['id']
        if obj_id not in enriched_data:
            image_path = os.path.join(image_dir, f"{obj_id}_bguw.png")
            if os.path.exists(image_path):
                missing.append(obj_id)
    
    print(f"Total chairs missing with images: {len(missing)}")
    
    # Split into 6 shards
    num_shards = 6
    shard_size = (len(missing) + num_shards - 1) // num_shards
    shards = [missing[i:i + shard_size] for i in range(0, len(missing), shard_size)]
    
    # Save shards to JSON files
    for i, shard in enumerate(shards):
        filename = f"shard_{i}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(shard, f, indent=2)
        print(f"Created {filename} with {len(shard)} chairs.")

if __name__ == "__main__":
    create_shards()
