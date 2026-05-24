"""Built-in tools for the default agent."""

from agent.tools.grep import tool as grep_tool
from agent.tools.ls import tool as ls_tool

tools = [ls_tool, grep_tool]
