import sys, asyncio, io
sys.path.insert(0, r"C:\ChillBot")
from utils.mcp_client import MCPClient

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

async def t():
    client = MCPClient()
    await client.connect(command=sys.executable, args=[r'C:\ChillBot\servers\info_server.py'], alias='info')
    await client.discover_tools()
    raw = await client.call_tool('book_recommend', {'topic': 'suggest me a sci fci book '})
    # Use agent's deterministic formatter
    from agent import format_book_result
    formatted = format_book_result(raw)
    print('RAW:', raw)
    print('\nFORMATTED:\n', formatted)
    await client.close()

asyncio.run(t())
