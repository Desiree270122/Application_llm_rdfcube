import os
import pandas as pd
from rdflib import Graph
from flask import Flask, render_template
import streamlit as st
from langchain.llms import OpenAI
import re

# Configurer la clé API OpenAI
os.environ["OPENAI_API_KEY"] = "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"
def generate_response(prompt):
    llm = OpenAI(openai_api_key=os.environ["OPENAI_API_KEY"], temperature=0.7, max_tokens=1024)
    response = llm(prompt)
    return response

# Charger les données RDF

def load_rdf_data(folder_path):
    combined_graph = Graph()
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.ttl'):  # ou '.rdf', '.nt', etc.
            file_path = os.path.join(folder_path, filename)
            g = Graph()
            g.parse(file_path, format='turtle')  # ou le format approprié
            combined_graph += g
    
    return combined_graph


def extract_details_from_question(question):
    course_pattern = r"(Mathématiques|Science|Géographie|Histoire|Chimie|Technologie|Français|Anglais|Trigonométrie)"
    class_pattern = r"(Première Année|Deuxième Année|Troisième Année|Quatrième Année|Cinquième Année|Sixième Année)"
    year_pattern = r"\b(2019|2020|2021|2022|2023)\b"

    course = re.search(course_pattern, question)
    class_name = re.search(class_pattern, question)
    year = re.search(year_pattern, question)

    return (course.group(0) if course else None, 
            class_name.group(0) if class_name else None, 
            year.group(0) if year else None)

def refine_question_with_llm(question):
    prompt = f"Reformule la question suivante pour qu'elle soit plus claire et précise : {question}"
    refined_question = generate_response(prompt)
    return refined_question

def execute_sparql_query(graph, query):
    from rdflib.plugins.sparql import prepareQuery
    results = graph.query(prepareQuery(query))
    return results

   # utilisation du streamlit
def main():
    st.title("Application LLM + RDF Cube")

    # Chemin du dossier contenant les fichiers RDF
    folder_path = r'C:\Users\Nael_Gaizka\Downloads\Activity-Ontology-main'
    combined_graph = load_rdf_data(folder_path)
    
    st.sidebar.header("Instructions")
    st.sidebar.write("""
        - Entrez une question concernant les performances éducatives.
        - L'application utilise un modèle de langage pour reformuler la question et extraire des détails.
        - Les données sont ensuite analysées à l'aide d'une requête SPARQL.
    """)
    
    # Entrée utilisateur pour la question
    question = st.text_input("Entrez votre question :")

    if question:
        # Reformuler la question
        refined_question = refine_question_with_llm(question)
        st.write(f"Question reformulée : {refined_question}")
        
        # Extraire les détails de la question reformulée
        course, class_name, year = extract_details_from_question(refined_question)
        
        if course and class_name and year:
            sparql_query = f"""
            PREFIX edu: <http://example.org/education/>
            PREFIX cube: <http://purl.org/linked-data/cube#>

            SELECT (AVG(?score) as ?averageScore)
            WHERE {{
              ?observation a cube:Observation ;
                           edu:Year "{year}"^^<http://www.w3.org/2001/XMLSchema#gYear> ;
                           edu:Subject "{course}" ;
                           edu:Class "{class_name}" ;
                           edu:Score ?score .
            }}
            """
            
            # Exécuter la requête SPARQL
            results = execute_sparql_query(combined_graph, sparql_query)
            average_score = next(results)[0] if results else "Aucune donnée trouvée"
            st.write(f"Le score moyen en {course} pour la {class_name} en {year} est : {average_score}")
            
            # Générer une analyse avec le LLM
            prompt = f"La requête en langage naturel est : {refined_question}\n\nLa réponse obtenue est : {average_score}\n\n" \
                     "Peux-tu fournir une analyse de cette donnée et des recommandations pour améliorer la performance de cette classe ?"
            response = generate_response(prompt)
            st.write("Analyse et recommandations :")
            st.write(response)
        else:
            st.write("Le LLM n'a pas pu extraire toutes les informations nécessaires. Veuillez reformuler votre question.")
    
if __name__ == "__main__":
    main()
