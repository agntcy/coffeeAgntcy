import asyncio

from graph.graph import ExchangeGraph


async def main():
  exchange_graph = ExchangeGraph()
  input_payload = {
    "location": "Antigua, Guatemala",
    "season": "harvest"
  }
  result = await exchange_graph.serve(input_payload)
  print(result)

if __name__ == '__main__':
    asyncio.run(main())
