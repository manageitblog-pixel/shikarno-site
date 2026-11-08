# Мінімальний MCP-сервер для відео «Конектори від А до Я»: офіційний курс НБУ.
from mcp.server import MCPServer
import json, urllib.request

mcp = MCPServer("nbu")

@mcp.tool()
def kurs_nbu(valuta: str = "USD") -> str:
    """Офіційний курс гривні НБУ на сьогодні. valuta — код: USD, EUR, PLN..."""
    url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={valuta.upper()}&json"
    d = json.load(urllib.request.urlopen(url, timeout=15))
    if not d:
        return f"Валюту {valuta} не знайдено"
    r = d[0]
    return f"{r['txt']} ({r['cc']}): {r['rate']} грн, дата {r['exchangedate']}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
