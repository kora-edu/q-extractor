from r2r import R2RClient

client = R2RClient("http://localhost:7272")
# when using auth, do client.login(...)
search_mode = "advanced"

ingest_response = client.documents.create(
    file_path="./JBdata5_updated.json",
    ingestion_mode="fast"
)

response = client.retrieval.agent(
        message={  
            "role": "user", "content": "Generate an integration question example with its respective answer",
    
        },

    search_settings={
         "graph_settings": {
            "enabled": "True",
            },
        "use_hybrid_search": True,
        #"search_strategy": "hyde",
        #"use_semantic_search": True,
       
        "limit": 10,
        "chunk_settings": {  # Correct indentation here
            "limit": 20,  # separate limit for chunk vs. graph
        },
    },
    rag_generation_config={
        "stream": False,
        "temperature": 0.2,
        "max_tokens": 500
    },
    include_title_if_available=True,
   
)
if "error" in response:
    print(f"Error occurred: {response['error']}")