import asyncio
from pathlib import Path

from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

from Backend.phoenix_tracing import flush_phoenix_traces, setup_phoenix_tracing


load_dotenv(override=True)

project_root = Path(__file__).resolve().parents[1]
server_params = {
	"command": "uv",
	"args": [
		"run",
		"--directory",
		str(project_root),
		"-m",
		"Backend.Jaguars_DB_Invoke",
	],
}

instructions = """You are the Jaguars Cricket Club assistant.
Use the MCP tools for club, player, performance, and fixture information.
When the user asks for ESPNcricinfo cricket records, use the get_cricinfo_records
tool and answer from its saved Markdown content. This content is a crawl, not live data.
When the user asks who has the most ODI runs, for ODI run rankings, or a player's
position in those rankings, use the get_most_odi_runs tool. Its data is a saved
snapshot, not live data.
The initial database records are demo data, not verified real club records.
Do not invent details that are missing from the database.
"""

async def main() -> None:
	request = input("Ask the Jaguars Cricket Club assistant: ").strip()
	if not request:
		print("Please enter a question.")
		return
	# Install the Phoenix exporter and OpenAI Agents instrumentation before running the agent.
	setup_phoenix_tracing()
	try:
		async with MCPServerStdio(
			params=server_params, client_session_timeout_seconds=60
		) as mcp_server:
			agent = Agent(
				name="jaguars_cricket_assistant",
				instructions=instructions,
				model="gpt-5.4-mini",
				mcp_servers=[mcp_server],
			)
			with trace("jaguars_cricket_club"):
				result = await Runner.run(agent, request)
			print(result.final_output)
	finally:
		# Flush the CLI trace before this one-shot process exits.
		flush_phoenix_traces()


if __name__ == "__main__":
	asyncio.run(main())
