import asyncio
import websockets
import sys

async def test_websocket():
    try:
        async with websockets.connect('ws://localhost:8000/ws/game_state') as ws:
            print('WebSocket connecte')
            msg = await asyncio.wait_for(ws.recv(), timeout=2)
            print('Message recu:', msg[:100])
            return True
    except Exception as e:
        print('Erreur:', e)
        return False

if __name__ == '__main__':
    success = asyncio.run(test_websocket())
    sys.exit(0 if success else 1)