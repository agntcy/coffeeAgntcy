import asyncio

from graph.graph import ExchangeGraph


async def main():
  exchange_graph = ExchangeGraph()
  location = input("Enter a location: ")
  season = input("Enter a season: ")
  input_payload = {
    "location": location,
    "season": season
  }
  result = await exchange_graph.serve(input_payload)
  print(result)

if __name__ == '__main__':
    asyncio.run(main())
