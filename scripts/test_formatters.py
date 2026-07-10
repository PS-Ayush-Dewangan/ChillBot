import sys, asyncio
sys.path.insert(0, r"C:\ChillBot")
from utils.mcp_client import MCPClient

async def t():
    client = MCPClient()
    # Connect both info and fun servers so all tools are available
    await client.connect(command=sys.executable, args=[r'C:\ChillBot\servers\info_server.py'], alias='info')
    await client.connect(command=sys.executable, args=[r'C:\ChillBot\servers\fun_server.py'], alias='fun')
    await client.discover_tools()
    raw = await client.call_tool('get_weather_by_city', {'city':'Ahmedabad'})
    from agent import format_weather_result
    print('WEATHER:', format_weather_result(raw))
    raw = await client.call_tool('recommend_movie', {'genre':'horror'})
    from agent import format_movie_result
    print('MOVIE:', format_movie_result(raw))
    raw = await client.call_tool('random_joke', {})
    from agent import format_joke_result
    print('JOKE:', format_joke_result(raw))
    raw = await client.call_tool('motivation_quote', {})
    from agent import format_quote_result
    print('QUOTE:', format_quote_result(raw))
    await client.close()

asyncio.run(t())
