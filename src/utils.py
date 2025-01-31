import re
from typing import List
from langchain.tools import Tool

def clean_sparql_query(query: str) -> str:
    cleaned_query = query.replace('```sparql\n', '')
    cleaned_query = cleaned_query.replace('\n```', '')
    cleaned_query = cleaned_query.replace('```', '')
    cleaned_query = cleaned_query.replace('\n', ' ')
    cleaned_query = cleaned_query.strip("'")
    cleaned_query = cleaned_query.strip()
    cleaned_query = cleaned_query.replace("\\'", "'")
    cleaned_query = cleaned_query.replace('\\"', '"')
    cleaned_query = cleaned_query.replace("\\\\", "\\")
    cleaned_query = re.sub(r"['\"]\s*$", "", cleaned_query)
    cleaned_query = cleaned_query.replace("\\n", " ")
    return cleaned_query

def find_tool_by_name(tools: List[Tool], tool_name: str) -> Tool:
    for tool in tools:
        if tool.name == tool_name:
            return tool
        
    raise ValueError(f"Tool with the tool name {tool_name} not found")