import json
import os
import glob

def merge_shards():
    main_file = 'STOLAR/enriched_chairs.json'
    
    with open(main_file, 'r', encoding='utf-8') as f:
        main_data = json.load(f)
    
    shard_files = glob.glob('STOLAR/enriched_chairs_shard_*.json')
    print(f"Found {len(shard_files)} shard files.")
    
    new_entries = 0
    for shard_file in shard_files:
        with open(shard_file, 'r', encoding='utf-8') as f:
            shard_data = json.load(f)
        
        for obj_id, data in shard_data.items():
            if obj_id not in main_data:
                main_data[obj_id] = data
                new_entries += 1
            else:
                # Optional: update if shard data is newer?
                # For now, just keep original if conflict
                pass
    
    if new_entries > 0:
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        print(f"Merged {new_entries} new entries into {main_file}. Total entries: {len(main_data)}")
        
        # Delete shard files after merge
        for shard_file in shard_files:
            try:
                os.remove(shard_file)
                print(f"Deleted {shard_file}")
            except Exception as e:
                print(f"Error deleting {shard_file}: {e}")
    else:
        print("No new entries to merge.")
    
    # Run sync script
    os.system("python STOLAR/enrich_db.py")

if __name__ == "__main__":
    merge_shards()
