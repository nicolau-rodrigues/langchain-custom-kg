
from langchain.prompts import PromptTemplate

ORCHESTRATION_TEMPLATE = """
You are an orchestration agent, and your final goal is to generate a response quering a triple store, considering the user input.
Think step by step, and call the necessary tools to achieve the final goal.
1- Analise the user input and check if there are terms that may be related to instances of classes of properties of the ontology.
2- If you conclude that the user input is related to instances of classes or properties of the ontology, call the Similarity Search Tool to get the URI of those instances.
3- Consider the URI of the instances and call the Query Generation Tool to generate the SPARQL.
4- Consider also the templates that you have available and the user input to generate the query.
The query_template you should provide to the Query Generation Tool is: {query_template} 
And the user_input: {user_input}

5- Use Query Validation Tool to validate the syntax and prefixes on the query. DO NOT EXECUTE THE QUERY BEFORE VALIDATING IT. 
6- ONLY IF THE QUERY IS INVALID, call the Query Fixing Agent to fix the query. 
7- Finally, format the response from the data received using the following guidelines:

BEGIN!
"""
ORCHESTRATION_PROMPT = PromptTemplate(
    input_variables=["user_input", "query_template"],
    template=ORCHESTRATION_TEMPLATE,
)

ORCHESTRATION_TEMPLATE_V2 = """
You are an orchestration agent, and your final goal is to generate a response quering a triple store, considering the user input.

Think step by step, and call the necessary tools to achieve the final goal.

FIRST, use the Query Generation Tool to generate SPARQL query based on the user input.
SECOND, use Query Validation Tool to validate the syntax and prefixes on the query. DO NOT EXECUTE THE QUERY BEFORE VALIDATING IT. 
THIRD, in case you receive an error from the Query Generation Agent, call the Query Fixing Tool, passing the generated query and the error message to it, to fix the query.
FOURTH, ONLY IF THE QUERY IS VALID, call the Query Execution Tool to execute the query and get the results from the triple store.  
FINALLY, use the Format Response Tool to format the response and generate the final answer.

The user input is: {user_input}
The tools you have available are: {tools}
The name of the tools are: {tool_names}
BEGIN!
"""
ORCHESTRATION_PROMPT_V2 = PromptTemplate(
    input_variables=["user_input", "tools", "tool_names"],
    template=ORCHESTRATION_TEMPLATE_V2,
)

HWCHASE17_REACT_TEMPLATE = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:   

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

HWCHASE17_REACT_PROMPT = PromptTemplate(
    input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
    template=HWCHASE17_REACT_TEMPLATE,
)

HWCHASE17_REACT_TEMPLATE_V2 = """
You are responsible to answer the following question as best as you can. 

Think step by step:
FIRST, use the Query Generation Tool to generate SPARQL query based on the user input.
SECOND, use Query Validation Tool to validate the syntax and prefixes on the query. DO NOT EXECUTE THE QUERY BEFORE VALIDATING IT. 
THIRD, in case you receive an error from the Query Generation Agent, call the Query Fixing Tool, passing the generated query and the error message to it, to fix the query.
FOURTH, ONLY IF THE QUERY IS VALID, call the Query Execution Tool to execute the query and get the results from the triple store.  
FINALLY, use the Format Response Tool to format the response and generate the final answer.

You You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

HWCHASE17_REACT_PROMPT_V2 = PromptTemplate(
    input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
    template=HWCHASE17_REACT_TEMPLATE_V2,
)


HWCHASE17_REACT_TEMPLATE_V3 = """
You are responsible to answer the following question as best as you can. 

Think step by step:
FIRST, use the Query Generation Tool to generate SPARQL query based on the user input.
SECOND, use Query Validation Tool to validate the syntax and prefixes on the query. DO NOT EXECUTE THE QUERY BEFORE VALIDATING IT. 
THIRD, in case you receive an error from the Query Generation Agent, call the Query Fixing Tool, passing the generated query and the error message to it, to fix the query.
FOURTH, ONLY IF THE QUERY IS VALID, call the Query Execution Tool to execute the query and get the results from the triple store.  
FINALLY, use the Format Response Tool to format the response and generate the final answer.

You You have access to the following tools:

{tools}

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

HWCHASE17_REACT_PROMPT_V3 = PromptTemplate(
    input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
    template=HWCHASE17_REACT_TEMPLATE_V3,
)


GRAPHDB_SPARQL_GENERATION_TEMPLATE = """
Write a SPARQL SELECT query for querying a graph database.
The ontology schema delimited by triple backticks in Turtle format is:
```
{schema}
```
Use only the classes and properties provided in the schema to construct the SPARQL query.
Do not use any classes or properties that are not explicitly provided in the SPARQL query.
Include all necessary prefixes.
Do not include any explanations or apologies in your responses.
Do not wrap the query in backticks.
Do not include any text except the SPARQL query generated.
The question delimited by triple backticks is:
```
{prompt}
```
When you have finished writing the query, use Query Validation Tool to validate the syntax and prefixes on the query. 
DO NOT EXECUTE THE QUERY BEFORE VALIDATING IT.
In case of errors you need return to who asked the question, providing the error messages, so that the caller may fix the query.
In case of success you must execute the query and return the results.
"""
GRAPHDB_SPARQL_GENERATION_PROMPT = PromptTemplate(
    #input_variables=["schema", "sparql_query_template", "prompt"],
    input_variables=["schema", "prompt"],
    template=GRAPHDB_SPARQL_GENERATION_TEMPLATE,
)

GRAPHDB_SPARQL_FIX_TEMPLATE = """
This following SPARQL query delimited by triple backticks
```
{generated_sparql}
```
is not valid.
The error delimited by triple backticks is
```
{error_message}
```
Give me a correct version of the SPARQL query.
Do not change the logic of the query.
Do not include any explanations or apologies in your responses.
Do not wrap the query in backticks.
Do not include any text except the SPARQL query generated.
The ontology schema delimited by triple backticks in Turtle format is:
```
{schema}
```
"""

GRAPHDB_SPARQL_FIX_PROMPT = PromptTemplate(
    input_variables=["error_message", "generated_sparql", "schema"],
    template=GRAPHDB_SPARQL_FIX_TEMPLATE,
)

GRAPHDB_QA_TEMPLATE = """Task: Generate a natural language response from the results of a SPARQL query.
You are an assistant that creates well-written and human understandable answers.
The information part contains the information provided, which you can use to construct an answer.
The information provided is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make your response sound like the information is coming from an AI assistant, but don't add any information.
Don't use internal knowledge to answer the question, just say you don't know if no information is available.
Information:
{context}

Question: {prompt}
Helpful Answer:"""
GRAPHDB_QA_PROMPT = PromptTemplate(
    input_variables=["context", "prompt"], template=GRAPHDB_QA_TEMPLATE
)