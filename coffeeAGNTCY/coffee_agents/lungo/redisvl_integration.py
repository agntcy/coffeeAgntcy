import json
import sys

from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.schema import IndexSchema
from sentence_transformers import SentenceTransformer

index_name = "auction_paths"
# load and prepare the model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

def initialize_index() -> SearchIndex:
    schema = IndexSchema.from_dict(
        {
            "index": {
                "name": index_name,
                "prefix": "auction:path:",
                "storage_type": "hash"
            },
            "fields": [
                {
                    "name": "prompt",
                    "type": "text",
                    "attrs": {
                        "weight": "1.0",
                        "sortable": False
                    }
                },
                {
                    "name": "route",
                    "type": "text",  # Store as JSON string
                    "attrs": {
                         "weight": "1.0",
                        "sortable": False
                    }
                },
                {
                    "name": "agent_names",
                    "type": "tag",  # For filtering by specific agents
                    "attrs": {
                        "separator": ","
                    }
                },
                {
                    "name": "text_embedding",
                    "type": "vector",
                    "attrs": {
                        "algorithm": "flat",
                        "dims": 384,
                        "distance_metric": "cosine",
                        "datatype": "float32"
                    }
                }
            ]
        }
    )
    # create the index
    index = SearchIndex(schema)
    index.connect("redis://localhost:6379")
    index.create(overwrite=True)
    print("index created")
    return index

def load_data(json_file_path, index):
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} records")
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file - {e}")
        sys.exit(1)

    records = []
    for item in data:
        embedding = model.encode(item["prompt"])
        
        # Extract agent names for tag field (useful for filtering)
        agent_names = ",".join([agent["agent_name"] for agent in item["route"]])

        record = {
            "prompt": item["prompt"],
            "route": json.dumps(item["route"]),  # Serialize the route array as JSON string
            "agent_names": agent_names,
            "text_embedding": embedding.tobytes()
        }

        records.append(record)

    index.load(records)
    print(f"Indexed {len(records)} records")

def search_similar(index, query_text: str, num_results: int = 1):
    """Search for similar prompts and return their routes"""
    embedding = model.encode(query_text)
    
    query = VectorQuery(
        vector=embedding.tobytes(),
        vector_field_name="text_embedding",
        return_fields=["prompt", "route", "agent_names"],
        num_results=num_results
    )
    results = index.query(query)
    return results

def parse_route(route_json: str) -> list[dict]:
    """Parse the route JSON string back to a list of dicts"""
    return json.loads(route_json)

if __name__ == "__main__":
    # Load the data
    index = initialize_index()
    load_data("mock_lungo_paths_data.json", index)
    
    query_text = "I want the inventory of all the farms"
    
    results = search_similar(index, query_text)
    print(f"Found {len(results)} results:\n")

    for result in results:
        print(f"Prompt: {result['prompt']}")
        print(f"Agents: {result['agent_names']}")
        
        # Parse route back to structured data
        route = parse_route(result['route'])
        print(f"Route:")
        for step in route:
            status = "✓" if step["success"] else "✗"
            print(f"  {status} {step['agent_name']}")
        
        print(f"Score: {result.get('vector_distance', 'N/A')}\n")