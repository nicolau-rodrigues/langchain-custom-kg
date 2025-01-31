import os
import re
import sys
import requests
import yaml
from rdflib import Graph
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from prompt_templates import GRAPHDB_QA_PROMPT, GRAPHDB_SPARQL_FIX_PROMPT, GRAPHDB_SPARQL_GENERATION_PROMPT

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import clean_sparql_query

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import nltk

# Verificar se os pacotes já estão instalados antes de baixá-los
nltk_data_path = os.path.join(os.getenv("APPDATA"), "nltk_data")

if not os.path.exists(nltk_data_path):
    os.makedirs(nltk_data_path)

nltk.data.path.append(nltk_data_path)

# Baixar os pacotes necessários, se não estiverem presentes
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)

_ontology_instance = None

def load_ontology(ontology_path: str) -> Graph:
    global _ontology_instance
    if _ontology_instance:
        return _ontology_instance
    else:
        _ontology_instance = Graph()
        _ontology_instance.parse(ontology_path, format="turtle")
        print(f"Ontology loaded with {len(_ontology_instance)} triples.")
        return _ontology_instance

def ontology_to_string(ontology: Graph) -> str:
    return ontology.serialize(format="turtle")

def get_classes(user_input: str, ontology: Graph = _ontology_instance):
    if not ontology:
        ontology = load_ontology(os.getenv("ONTOLOGY_PATH"))

    query = """
    SELECT DISTINCT ?cls WHERE {
        ?cls a owl:Class .
        FILTER(CONTAINS(LCASE(STR(?cls)), LCASE(?term)))
    }
    """
    terms = extract_terms(user_input)
    classes = []
    for term in terms:
        for row in ontology.query(query, initBindings={'term': term}):
            classes.append(str(row.cls))
    return classes

def get_properties(user_input: str, ontology: Graph = _ontology_instance):
    if not ontology:
        ontology = load_ontology(os.getenv("ONTOLOGY_PATH"))

    query = """
    SELECT DISTINCT ?property WHERE {
        ?property a rdf:Property .
        FILTER(CONTAINS(LCASE(STR(?property)), LCASE(?term)))
    }
    """
    terms = extract_terms(user_input)
    properties = []
    for term in terms:
        for row in ontology.query(query, initBindings={'term': term}):
            properties.append(str(row.property))
    return properties

def get_relationships(user_input: str, ontology: Graph = _ontology_instance):
    if not ontology:
        ontology = load_ontology(os.getenv("ONTOLOGY_PATH"))
    
    query = """
    SELECT DISTINCT ?subject ?predicate ?object WHERE {
        ?subject ?predicate ?object .
        FILTER(CONTAINS(LCASE(STR(?subject)), LCASE(?term)) ||
               CONTAINS(LCASE(STR(?predicate)), LCASE(?term)) ||
               CONTAINS(LCASE(STR(?object)), LCASE(?term)))
    }
    """
    terms = extract_terms(user_input)
    relationships = []
    for term in terms:
        for row in ontology.query(query, initBindings={'term': term}):
            relationships.append((str(row.subject), str(row.predicate), str(row.object)))
    return relationships

def extract_prefixes(query: str) -> set:
    """
    Extrai os prefixos necessários de uma consulta SPARQL.
    
    Args:
        query (str): A consulta SPARQL.
    
    Returns:
        set: Um conjunto de prefixos necessários.
    """
    # Encontrar todos os URIs na consulta que precisam de prefixos
    uris = re.findall(r'\b\w+:\w+\b', query)
    # Extrair os prefixos dos URIs
    prefixes = {uri.split(':')[0] for uri in uris}
    return prefixes

def validate_sparql_query(query: str) -> bool:
    """
    Valida se a consulta SPARQL é sintaticamente válida.
    
    Args:
        query (str): A consulta SPARQL a ser validada.
    
    Returns:
        bool: True se a consulta for válida, False caso contrário.
    """
    try:
        #parseQuery(query)
        required_prefixes = extract_prefixes(query)
        defined_prefixes = re.findall(r'PREFIX\s+(\w+):', query, re.IGNORECASE)
        missing_prefixes = required_prefixes - set(defined_prefixes)

        if len(missing_prefixes) > 0:
            print("Missing prefixes:", missing_prefixes)

            ontology = load_ontology(os.getenv("ONTOLOGY_PATH"))

            for prefix in missing_prefixes:
                namespace = ontology.namespace_manager.store.namespace(prefix)
                if namespace:
                    query = f"PREFIX {prefix}: <{namespace}>\n" + query
                    print(f"Added prefix {prefix} to the query.")
        
        return True
    except Exception:
        return False

# Templates functions:
def read_sparql_templates(file_path: str):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data['templates']

def find_closest_template(user_input: str) -> dict:
    
    templates = read_sparql_templates(os.getenv("SPARQL_TEMPLATES_PATH"))
    # Combine descriptions and tags into a single string for each template
    template_texts = [
        template['description'] + ' ' + ' '.join(template['tags'])
        for template in templates
    ]
    
    # Add the user input to the list of texts
    texts = template_texts + [user_input]
    
    # Vectorize the texts using TF-IDF
    vectorizer = TfidfVectorizer().fit_transform(texts)
    vectors = vectorizer.toarray()
    user_vector = vectors[-1].reshape(1, -1)
    template_vectors = vectors[:-1]

    # Compute cosine similarity between the user input and each template
    cosine_similarities = cosine_similarity(user_vector, template_vectors)
    
    # Find the index of the most similar template
    closest_index = cosine_similarities.argmax()
    
    return templates[closest_index]

# NLP functions:
def extract_terms(user_input: str):
    # Tokenizar a entrada do usuário
    tokens = nltk.word_tokenize(user_input)
    
    # Obter as tags de parte do discurso (POS tags)
    pos_tags = nltk.pos_tag(tokens)
    
    # Extrair termos relevantes (substantivos, adjetivos, etc.)
    terms = [word for word, pos in pos_tags if pos in ["NN", "NNS", "NNP", "NNPS", "JJ"]]
    
    return terms


# GraphDB functions:
def execute_sparql_query(query: str, endpoint: str = os.getenv("REPO_URL")) -> str:
    headers = {
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "query": clean_sparql_query(query)
    }
    try:
        response = requests.post(endpoint, headers=headers, data=data)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        return f"Query failed with exception: {e}. THE QUERY WAS: {data['query']}"

def fix_sparql_query(generated_sparql: str, error_message:str = None) -> str:

    llm = ChatOpenAI(
        temperature = 0,
        model=os.getenv("LLM_MODEL")
    )
    
    chain = GRAPHDB_SPARQL_FIX_PROMPT | llm
    
    result = chain.invoke(
        GRAPHDB_SPARQL_FIX_PROMPT.format_prompt(
            error_message=error_message, 
            generated_sparql=generated_sparql, 
            schema=ontology_to_string(load_ontology(os.getenv("ONTOLOGY_PATH")))
        )
    )
    cleaned_fixed_query = clean_sparql_query(result.content)
    return cleaned_fixed_query

def format_response(query_result: str, prompt: str = None) -> str:
    
    llm = ChatOpenAI(
        temperature = 0,
        model=os.getenv("LLM_MODEL")
    )
    chain = GRAPHDB_QA_PROMPT | llm
    formatted_prompt = chain.invoke({"context": query_result, "prompt": prompt})
    
    return formatted_prompt

def generate_sparql_query(user_input: str) -> str:

    llm = ChatOpenAI(
        temperature = 0,
        model=os.getenv("LLM_MODEL")
    )
    chain = GRAPHDB_SPARQL_GENERATION_PROMPT | llm

    #result = chain.invoke({"schema": ontology_to_string(load_ontology(os.getenv("ONTOLOGY_PATH"))), "sparql_query_template":query_template,"prompt": user_input})
    result = chain.invoke({"schema": ontology_to_string(load_ontology(os.getenv("ONTOLOGY_PATH"))),"prompt": user_input})
    cleaned_generated_query = clean_sparql_query(result.content)
    return cleaned_generated_query

def similarity_search(term: str) -> dict:
    """
    Usefull to similarity search ONLY when you find instances in the input provided in GraphDB.
    Similarity searchs should consider as 'term' only the terms that represents the instance, not complete sentences.
    Example of similarity_search: in the input 'data products that cover Customers', you have to consider only 'Customers' as the input term.

    Args:
        term (str): The term to search for in the GraphDB.

    Returns:
        dict: A dictionary containing `documentID` and `class` values from the SPARQL query.

    """
    
    # Endpoint para SPARQL queries
    SPARQL_ENDPOINT = (
        os.getenv("GRAPHDB_BASE_URL") + "/repositories/" + os.getenv("REPOSITORY")
    )

    term = term.strip()
    term = " ".join(term.split())

    query = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX :<http://www.ontotext.com/graphdb/similarity/>
    PREFIX similarity-index:<http://www.ontotext.com/graphdb/similarity/instance/>
    PREFIX pubo: <http://ontology.ontotext.com/publishing#>

    SELECT distinct ?documentID ?class {{
        ?search a similarity-index:{os.getenv("SIMILARITY_SEARCH_INDEX_NAME")} ;
            :searchTerm "{term}";
            :searchParameters "-searchresultsminscore 0.99";
            :documentResult ?result .
        ?result :value ?documentID ;
                :score ?score.
        ?documentID rdf:type ?class .
    }}
    """

    headers = {"Content-Type": "application/sparql-query", "Accept": "application/json"}

    try:
        response = requests.post(SPARQL_ENDPOINT, data=clean_sparql_query(query), headers=headers)
        response.raise_for_status()  # Levanta uma exceção se o status não for 2xx
        data = response.json()
        result_dict = {
            "documentID": [
                binding["documentID"]["value"]
                for binding in data["results"]["bindings"]
            ],
            "class": [
                binding["class"]["value"] for binding in data["results"]["bindings"]
            ],
        }
        return result_dict

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}. Query: {query}")
    except ValueError as e:
        print(f"Error executing query: {e}")
