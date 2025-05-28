from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph.graph import ExchangeGraph
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
# Add CORS middleware
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # Replace "*" with specific origins if needed
  allow_credentials=True,
  allow_methods=["*"],  # Allow all HTTP methods
  allow_headers=["*"],  # Allow all headers
)


exchange_graph = ExchangeGraph()

class PromptRequest(BaseModel):
  prompt: str

@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest):
  print(f"Received prompt: {request.prompt}")
  input_payload = {"prompt": request.prompt}
  try:
    result = await exchange_graph.serve(input_payload)
    return {"response": result}
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Run the FastAPI server using uvicorn
if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
