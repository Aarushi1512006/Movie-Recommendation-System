import httpx
import asyncio

async def test():
    try:
        # Forcing a simple get with high timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get("https://api.themoviedb.org/3/movie/popular?api_key=ed30dd9b1eca6bfb88e75c31cf987bac")
            print(f"Status: {r.status_code}")
            print(f"Content: {str(r.json())[:100]}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
