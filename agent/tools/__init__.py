"""Built-in tools for the default agent."""

from agent.tools.grep import grep as grep_tool
from agent.tools.ls import ls

tools = [ls, grep_tool]
