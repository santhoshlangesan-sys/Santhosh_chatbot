import asyncio
import json
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from fastmcp import FastMCP


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
mcp = FastMCP("Jaguars Database")
CRICINFO_RECORDS_PATH = Path(__file__).with_name("cricinfo-records.md")
MOST_RUNS_ODI_PATH = Path(__file__).with_name("Most-ODI-Runs.md")


def get_db_connection() -> mysql.connector.MySQLConnection:
    """Open and return a connection to the Jaguars MySQL database."""
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    missing = [
        name
        for name, value in (("MYSQL_USER", user), ("MYSQL_PASSWORD", password))
        if not value
    ]
    if missing:
        raise ValueError(
            "Set the following environment variables to connect to MySQL: "
            + ", ".join(missing)
        )

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=user,
        password=password,
        database="jaguars",
        connection_timeout=10,
    )


def _fetch_rows(
    query: str, parameters: tuple[str, ...] = ()
) -> list[dict[str, object]]:
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, parameters)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()


@mcp.tool()
async def list_players() -> str:
    """List the full Jaguars squad with each player's profile and statistics.

    Use this tool when the user asks to see all players, the squad, or compare
    statistics across the team. Returns a JSON object with a player count and
    each player's profile.
    """
    players = await asyncio.to_thread(
        _fetch_rows, "SELECT * FROM jaguars_stats ORDER BY Name"
    )
    return json.dumps(
        {"count": len(players), "players": players},
        indent=2,
        default=str,
    )


@mcp.tool()
async def get_player_details(player_name: str) -> str:
    """Get one Jaguars player's profile and statistics by name.

    Use this tool when the user asks about a specific player. Provide the
    player's name in `player_name`. Returns the player's details as JSON, or
    a JSON error if no matching player exists.
    """
    normalized_name = player_name.strip()
    if not normalized_name:
        return json.dumps({"error": "player_name must not be empty."})

    players = await asyncio.to_thread(
        _fetch_rows,
        "SELECT * FROM jaguars_stats WHERE Name = %s LIMIT 1",
        (normalized_name,),
    )
    if not players:
        return json.dumps(
            {"error": f"No player found with name '{normalized_name}'."}
        )
    return json.dumps({"player": players[0]}, indent=2, default=str)


@mcp.tool()
async def get_cricinfo_records() -> str:
    """Read the saved ESPNcricinfo records page as Markdown.

    Use this tool when the user asks for cricket records from ESPNcricinfo.
    The returned content is the locally saved crawl, not live data.
    """
    if not CRICINFO_RECORDS_PATH.is_file():
        raise FileNotFoundError(
            f"ESPNcricinfo records file not found: {CRICINFO_RECORDS_PATH}. "
            "Run Backend/crawl_cricinfo_records.py to create it."
        )

    content = CRICINFO_RECORDS_PATH.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"ESPNcricinfo records file is empty: {CRICINFO_RECORDS_PATH}")
    return content


@mcp.tool()
async def get_most_odi_runs() -> str:
    """Read the saved ESPNcricinfo most ODI runs table.

    Use this tool when the user asks who has the most ODI runs, asks for
    ODI run rankings, or requests a player's position in that list.
    The returned content is a saved snapshot, not live data.
    """
    if not MOST_RUNS_ODI_PATH.is_file():
        raise FileNotFoundError(
            f"Most ODI Runs file not found: {MOST_RUNS_ODI_PATH}."
        )

    content = MOST_RUNS_ODI_PATH.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"Most ODI Runs file is empty: {MOST_RUNS_ODI_PATH}")
    return content


if __name__ == "__main__":
    mcp.run(transport="stdio")