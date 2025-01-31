import os
from dotenv import load_dotenv

from prompt_templates import HWCHASE17_REACT_PROMPT, ORCHESTRATION_TEMPLATE
from langchain.agents.format_scratchpad import format_log_to_str

from tools import execute_sparql_query, find_closest_template, fix_sparql_query, format_response, generate_sparql_query, similarity_search, validate_sparql_query

load_dotenv()   

from langchain_core.tools.render import render_text_description
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain.agents import (
    create_react_agent,
    AgentExecutor,
)

def format_scratchpad(scratchpad):
    return format_log_to_str(scratchpad)

def preprocess_inputs(inputs):

    inputs["agent_scratchpad"] = format_scratchpad(inputs["intermediate_steps"])
    return inputs

def query_triple_store(user_prompt: str) -> str:
    
    orchestration_intermediate_steps = []

    llm = ChatOpenAI(
        temperature = 0,
        model=os.getenv("LLM_MODEL")
    )

    tools_for_agent = [
        Tool(
            name="Query Generation Tool",
            func=generate_sparql_query,
            description="Useful to generate the SPARQL query based on the user input and in the Sparql Query Template. Return the generated query as string.",	
        ),
        Tool(
            name="Query Execution Tool",
            func=execute_sparql_query,
            description="Useful when you need to execute the generated query and get the results from the triple store. Return the results as string.",	
        ),
        Tool(
            name="Syntax Validation Tool",
            func=validate_sparql_query,
            description="Useful when you need to validade the syntax and prefixes on the query. Example: function to verify if there are missing prefixes or wrong sparql syntax.",	
        ),
        Tool(
            name="Query Fixing Tool",
            func=fix_sparql_query,
            description="Useful when you need to fix invalid queries. Return the fixed query as string.",	
        ),
        Tool(
            name="Format Response Tool",
            func=format_response,
            description="Useful when you need to format the query response before returning to the user. Return the formatted response as string.",	
        ),
        Tool(
            name="Similarity Search Tool",
            func=similarity_search,
            description="Usefull to similarity search ONLY when you find terms in the input provided that corresponds to intances in GraphDB.",	
        ),
    ]

    agent = create_react_agent(
        llm=llm, 
        tools=tools_for_agent, 
        prompt=HWCHASE17_REACT_PROMPT.partial(
            tools=render_text_description(tools_for_agent),
            tool_names=", ".join([t.name for t in tools_for_agent]),
        ),
    )
    agent = (lambda x: preprocess_inputs(x)) | agent
    
    agent_executor = AgentExecutor(agent=agent, tools=tools_for_agent, verbose=True)

    closest_template = find_closest_template(user_prompt)

    try:
        result = agent_executor.invoke(
            {
                    "input": ORCHESTRATION_TEMPLATE.format(query_template=closest_template, user_input=user_prompt),
                    "agent_scratchpad": orchestration_intermediate_steps,
            }
        )
        orchestration_intermediate_steps.append(("Agent Step", str(result)))
        return result["output"]
    except Exception as e:
        result = f"I cannot answer this question. {str(e)}"
