import asyncio

from graph.graph import ExchangeGraph


async def main():
  exchange_graph = ExchangeGraph()
  user_prompt = "Sample user input for ExchangeGraph" # TODO Put sample user prompt here
  result, _ = await exchange_graph.serve(user_prompt)
  print(result)

if __name__ == '__main__':
    asyncio.run(main())
