# Langchain Custom KG

This project is an implementation of a custom SPARQL query tool using the Langchain library. It allows the generation, validation, correction, and execution of SPARQL queries on a GraphDB repository.

## Project Structure

- `orchestration_agent.py`: Main file that orchestrates the execution of SPARQL queries.
- `tools.py`: Contains auxiliary functions to generate, validate, correct, and execute SPARQL queries.
- `utils.py`: Contains utility functions, such as cleaning SPARQL queries.
- `prompt_templates.py`: Contains prompt templates used for generating SPARQL queries.
- `.env`: Configuration file containing environment variables required for the project execution.

## Requirements

- Python 3.8 or higher
- Libraries listed in `requirements.txt`

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/langchain-custom-kg.git
    cd langchain-custom-kg
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a [.env](http://_vscodecontentref_/0) file in the root directory of the project and add the necessary environment variables:
    ```env
    GRAPHDB_BASE_URL=<your_graphdb_base_url>
    REPOSITORY=<your_repository_name>
    LLM_MODEL=<your_llm_model>
    ONTOLOGY_PATH=<path_to_your_ontology_file>
    SIMILARITY_SEARCH_INDEX_NAME=<your_similarity_search_index_name>
    ```

## Usage

1. Run the [orchestration_agent.py](http://_vscodecontentref_/1) file to start the SPARQL query orchestration:
    ```bash
    python orchestration_agent.py
    ```

2. Example usage:
    ```python
    from orchestration_agent import query_triple_store

    user_prompt = "List all data products in the Services domain."
    sparql_query = query_triple_store(user_prompt)
    print(sparql_query)
    ```

## Functions

### `generate_sparql_query`

Generates a SPARQL query based on user input and a SPARQL query template.

### `validate_sparql_query`

Validates the syntax and prefixes of a SPARQL query.

### `fix_sparql_query`

Fixes invalid SPARQL queries.

### `execute_sparql_query`

Executes a SPARQL query and returns the results.

### `clean_sparql_query`

Cleans a SPARQL query by removing unnecessary characters and formatting issues.

## License

This project is licensed under the MIT License.