import asyncio
import os
from dotenv import load_dotenv

from slim_bindings import PyName
from common import create_slim_app

async def run_participant(secret: str):
    local_name = PyName("agntcy", "slimbrew", "coruscant-farm")
    slim_app = await create_slim_app(secret, local_name)
    async with slim_app:
        try:
            print(f"[participant] listening - locator: {local_name}")
            recv_session, data = await slim_app.receive()
            print(f"received session: {recv_session.id}")
            print(f"from: {recv_session.source_name}")
            print(f"to:   {recv_session.destination_name}")
            print(f"[group] {data.decode()}")
            try:
                while True:
                    recv_session, msg_rcv = await slim_app.receive(
                        session=recv_session.id
                    )
                    print(f"Received message in session {recv_session.id}: {msg_rcv.decode()}")
              

                    # reply to the group
                    reply = f"Hello from coruscant".encode()
                    print(f"sending {reply} to {recv_session.destination_name}")
                    await slim_app.publish(
                        recv_session, reply,  PyName("agntcy", "slimbrew", "moderator") 
                    )
            except Exception:
                print(f"receive listener error: {e!r}")
        except asyncio.CancelledError:
            print(f"receive listener cancelled")
            raise
        except Exception as e:
            print(f"receive listener error: {e!r}")
        
if __name__ == "__main__":
    load_dotenv()
    secret = os.environ.get("SLIM_SHARED_SECRET")
    if not secret:
        raise ValueError("SLIM_SHARED_SECRET environment variable is not set.")
    try:
        asyncio.run(run_participant(secret))
    except KeyboardInterrupt:
        print("Client interrupted by user.")
