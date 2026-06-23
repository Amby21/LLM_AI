#%%
import pandas as pd
import numpy as np
#%%
df_dataset = pd.read_csv('dataset.csv')
df_description = pd.read_csv("symptom_Description.csv")
df_precaution = pd.read_csv("symptom_precaution.csv")
df_severity = pd.read_csv("Symptom-severity.csv")

# %%
print("dataset.csv")
print(f"Shape{df_dataset.shape}")
print(f"Columns:{df_dataset.columns.tolist()}")
print(df_dataset.head(3))

print("\n=== symptom_severity.csv ===")
print(f"Shape: {df_severity.shape}")
print(df_severity.head(3))

print("\n=== symptom_Description.csv ===")
print(f"Shape: {df_description.shape}")
print(df_description.head(3))

print("\n=== symptom_precaution.csv ===")
print(f"Shape: {df_precaution.shape}")
print(df_precaution.head(3))

# %%
# Step 1: Wide to Long transformation of dataset.csv

symptoms_cols = [col for col in df_dataset.columns if col != 'Disease']

print(f"Disease column: Disease")
print(f"Symptoms colums ({len(symptoms_cols)}): {symptoms_cols}")
# %% Melt Wide to Long
df_long = df_dataset.melt(id_vars = ['Disease'], value_vars = symptoms_cols, var_name = 'Symptom_Position', value_name = 'Symptom')
print(f"\nBefore melt: {df_dataset.shape}")
print(f"After melt:  {df_long.shape}")
print(f"\nSample after melt:")
print(df_long.head(10))

# %% STEP 2 - CLEANING THE LONG FORM

#Remove rows where Symptom is empty/NaN
df_long = df_long.dropna(subset=['Symptom'])
df_long = df_long[df_long['Symptom'].str.strip() != '']

#%% Drop postion column
df_long = df_long.drop('Symptom_Position',axis=1)

#Clean Symptom names
df_long['Symptom'] = df_long['Symptom'].str.strip()
df_long['Disease'] = df_long['Disease'].str.strip()

df_long = df_long.drop_duplicates()
print(f"\nAfter cleaning: {df_long.shape}")
print(f"\nUnique diseases:  {df_long['Disease'].nunique()}")
print(f"Unique symptoms:  {df_long['Symptom'].nunique()}")
print(f"\nSample edges:")
print(df_long.head(10))

# %% Add severity weights to edges

df_severity.columns = df_severity.columns.str.strip()
df_severity['Symptom'] = df_severity['Symptom'].str.strip()

print(f"\nSeverity sample:")
print(df_severity.head(10))
# %%
df_edges = pd.merge(df_long,df_severity,on='Symptom',how='left')
median_severity = df_edges['weight'].median()
df_edges['weight'] = df_edges['weight'].fillna(median_severity)
print(f"\nEdges with severity weights:")
print(df_edges.head(10))
print(f"\nSeverity stats:")
print(df_edges['weight'].describe())
# %%
print(len(df_edges))
# %%
print("Disease list:")
print(df_long['Disease'].unique())
print(f"\nTop 10 diseases by symptom count:")
print(df_long.groupby('Disease')['Symptom'].count().sort_values(ascending=False).head(10))
# %% Building Knowledge graph.
import networkx as nx
# Create Directed Graph
G = nx.DiGraph()

# Add disease nodes with properties
print("Ading Disease nodes ...")
for _, row in df_description.iterrows():
    disease = row['Disease'].strip()
    description = row['Description'].strip() if 'Description' in row else ''
    G.add_node(disease, node_type='Disease', description=description)
print(f"Disease nodes added: {G.number_of_nodes()}")

#%% Add Symptom Nodes with properties
print("Ading Symptom nodes ...")  
unique_symptoms = df_edges['Symptom'].unique()

for symptom in unique_symptoms:
    severity = df_severity[df_severity['Symptom']== symptom]['weight'].values
    severity = severity[0] if len(severity) > 0 else 3

    G.add_node(symptom,node_type='Symptom',severity=float(severity))
print(f"Total nodes after symptoms: {G.number_of_nodes()}")

#%% Add SYMPTOM->DISEASE EDGES (Indicates relationship)
print("\nAdding INDICATES edges...")

for _, row in df_edges.iterrows():
    G.add_edge(
        row['Symptom'],
        row['Disease'],
        relationship = 'INDICATES',
        weight = float(row['weight'])
    )
print(f"INDICATES edges added: {G.number_of_edges()}")   

#%% Add disease -> precaution edges
print("\nAdding PRECAUTION edges...")
precaution_cols = [col for col in df_precaution.columns if col != 'Disease']

for _, row in df_precaution.iterrows():
    disease = row['Disease'].strip()
    for col in precaution_cols:
        if pd.notna(row[col]) and str(row[col]).strip():
            precaution = str(row[col]).strip()

            #Add precaution node if not exists
            if not G.has_node(precaution):
                G.add_node(precaution,node_type='Precaution')
            # Add edge
            G.add_edge(
                disease,
                precaution,
                relationship='PRECAUTION'
            )
# GRAPH SUMMARY
# ============================================================
print(f"\n=== Knowledge Graph Summary ===")
print(f"Total nodes:      {G.number_of_nodes()}")
print(f"Total edges:      {G.number_of_edges()}")

#Count by node type
node_types ={}
for node , data in G.nodes(data=True):
    ntype = data.get('node_type','Unknown')
    node_types[ntype] = node_types.get(ntype,0) + 1

print(f"\nNodes by type:")
for ntype, count in node_types.items():
    print(f"  {ntype}: {count}")

# Count by edge type
edge_types = {}
for u, v, data in G.edges(data=True):
    etype = data.get('relationship', 'Unknown')
    edge_types[etype] = edge_types.get(etype, 0) + 1

print(f"\nEdges by type:")
for etype, count in edge_types.items():
    print(f"  {etype}: {count}")
# %%
# Find the unknown node
unknown_nodes = [(n, d) for n, d in G.nodes(data=True) 
                 if d.get('node_type') == 'Unknown' 
                 or 'node_type' not in d]
print(f"Unknown nodes: {unknown_nodes}")
# %% Visualize SUBGRAPH
import matplotlib.pyplot as plt

def visualise_disease_subgraph(disease_name):
    """Show all symptoms connected to one disease"""

    #Get symptom nodes connected to the input disease
    symptom_nodes = [ n for n in G.predecessors(disease_name) if G.nodes[n].get('node_type')=='Symptom']

    #Get precaution nodes connected to the input disease
    precaution_nodes = [ n for n in G.successors(disease_name) if G.nodes[n].get('node_type')=='Precaution']

    # Build subgraph
    nodes_to_show = ([disease_name] + symptom_nodes + precaution_nodes)
    subgraph = G.subgraph(nodes_to_show)

        # Color nodes by type
    colors = []
    for node in subgraph.nodes():
        ntype = G.nodes[node].get('node_type')
        if ntype == 'Disease':
            colors.append('red')
        elif ntype == 'Symptom':
            colors.append('steelblue')
        else:
            colors.append('green')
    
    plt.figure(figsize=(14, 8))
    pos = nx.spring_layout(subgraph, seed=42)
    
    nx.draw_networkx_nodes(subgraph, pos, 
                          node_color=colors,
                          node_size=1500,
                          alpha=0.9)
    nx.draw_networkx_labels(subgraph, pos,
                           font_size=8,
                           font_weight='bold')
    nx.draw_networkx_edges(subgraph, pos,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=20)
    
    # Legend
    from matplotlib.patches import Patch
    legend = [
        Patch(color='red',       label='Disease'),
        Patch(color='steelblue', label='Symptom'),
        Patch(color='green',     label='Precaution')
    ]
    plt.legend(handles=legend, loc='upper left')
    plt.title(f'Knowledge Graph — {disease_name}')
    plt.axis('off')
    plt.tight_layout()
    plt.show()
    
    print(f"\n{disease_name}:")
    print(f"  Symptoms:    {len(symptom_nodes)}")
    print(f"  Precautions: {len(precaution_nodes)}")

visualise_disease_subgraph('Common Cold')
# %%
# # Naive scoring: just count matching symptoms
# Score(Disease) = number of matching symptoms
# # Problem: Common Cold has 17 symptoms
# # If patient matches 5 → 5/17 = 29% coverage
# # Rare disease has 4 symptoms
# # If patient matches 3 → 3/4 = 75% coverage
# # Rare disease should rank HIGHER ✅

# # Better scoring:
# Score(Disease) = Σ(symptom_weight) × coverage_ratio

# Where:
# symptom_weight = severity of each matching symptom
# coverage_ratio = matched_symptoms / total_disease_symptoms

# Example:
# Common Cold:  5 matches × avg_weight(3) × (5/17) = 4.4
# Rare Disease: 3 matches × avg_weight(5) × (3/4)  = 11.2
# Rare Disease ranks higher ✅
#%% DIAGNOSIS ENGINE
from difflib import SequenceMatcher

def fuzzy_match_symptom(input_term, threshold = 0.6):
    """Match input text to closest symptom node
    "mild fever" -> "fever" (exact after cleaning)
    "continous sneezing" → "continuous_sneezing" (fuzzy)
    """
    #Get all symptom nodes
    symptom_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'Symptom']
   
    input_clean = input_term.lower().strip()
    input_clean = input_clean.replace(' ','_') #graph stores symptoms with underscores

    best_match = None
    best_score = 0

    for symptom in symptom_nodes:
        symptom_clean = symptom.lower().strip()

        #exact match first
        if input_clean == symptom.clean:
            return symptom, 1.0
        
        score = SequenceMatcher(None,input_clean,symptom_clean).ratio()

        if score > best_score:
            best_score = score
            best_match = symptom

    if best_score >= threshold:
        return best_match,best_score
    else:
        return None, 0
#Extract symptoms from free text
def extract_symptoms_from_text(text):
    """Extract symptoms from free text input
    Input:  "patient has mild fever and continuous sneezing"
    Output: [('fever', 0.95), ('continuous_sneezing', 0.87)] """

    # get all symptom nodes for reference
    symptom_nodes = [n.lower().replace('_',' ') for n,d in G.nodes(data=True) if d.get('node_type') == 'Symptom']

    # Clean text
    text_clean = text.lower()
    text_clean = text_clean.replace(',',' ')
    text_clean = text_clean.replace('.',' ')
    # Remove common medical stop words
    stop_words = ['patient', 'has', 'have', 'with', 
                    'and', 'the', 'a', 'an', 'mild',
                    'severe', 'chronic', 'acute', 
                    'continuous', 'persistent', 'slight']

    matched_symptoms = []
    matched_names = set()

    symptom_nodes_sorted = sorted(symptom_nodes,key=len, reverse=True)

    for symptom in symptom_nodes_sorted:
        if symptom in text_clean:
            #Find canonical graph node name
            canonical = symptom.replace(' ','_')
            graph_nodes = [n for n in G.nodes() 
                        if n.lower() == canonical.lower()
                        or n.lower() == symptom.lower()]
            if graph_nodes and graph_nodes[0] not in matched_names:
                matched_symptoms.append((graph_nodes[0],1.0))
                matched_names.add(graph_nodes[0])
                text_clean = text_clean.replace(symptom, '')
    # Try single word matching on remaining text
    remaining_words = [w for w in text_clean.split() 
                        if w not in stop_words and len(w) > 3]
        
    for word in remaining_words:
        match, score = fuzzy_match_symptom(word, threshold=0.75)
        if match and match not in matched_names:
            matched_symptoms.append((match, score))
            matched_names.add(match)
        
    return matched_symptoms

#%%
def diagnose(text, top_n = 3):
    """Main Diagnosis function: 
    Input: Free text symptom description
    Output: Ranked list of diseases with scores."""
    print(f"\n{'='*50}")
    print(f"INPUT: {text}")
    print(f"{'='*50}")
    # Step 1: Extract symptoms
    matched_symptoms = extract_symptoms_from_text(text)

    if not matched_symptoms:
        return "No symptoms matched. Please describe symptoms more specifically."
    
    print(f"\n✅ Matched Symptoms:")
    for symptom, score in matched_symptoms:
        severity = G.nodes[symptom].get('severity', 3)
        print(f"  → {symptom} (match={score:.2f}, severity={severity})")
    
    # Step 2: Graph traversal — find candidate diseases
    disease_scores = {}
    disease_matched_symptoms = {}
    for symptom, match_score in matched_symptoms:
        if symptom not in G.nodes():
            continue
        
        #Get dieseases this symptom indicates
        for disease in G.successors(symptom):
            if G.nodes[disease].get('node_type') != 'Disease':
                continue

            #get edge weight (symptom severity)
            edge_data = G.get_edge_data(symptom,disease)
            weight = edge_data.get('weight',3)

            #Accumalate score
            if disease not in disease_scores:
                disease_scores[disease] = 0
                disease_matched_symptoms[disease] = []

            disease_scores[disease] += weight * match_score
            disease_matched_symptoms[disease].append(symptom)

    if not disease_scores:
        return "No diseases found for given symptoms."

    #Coverage Ratio Adjustment
    final_scores = {}
    for disease, score in disease_scores.items():

        total_symptoms = len([n for n in G.predecessors(disease) if G.nodes[n].get('node_type') == 'Symptom'])
        matched = len(disease_matched_symptoms[disease])
        # Coverage ratio
        coverage = matched / total_symptoms if total_symptoms > 0 else 0
        
        # Final score = raw score × coverage
        final_scores[disease] = {
            'score': score * coverage,
            'raw_score': score,
            'coverage': coverage,
            'matched_symptoms': disease_matched_symptoms[disease],
            'total_symptoms': total_symptoms,
            'matched_count': matched
        }
    
    # Step 4: Rank diseases
    ranked = sorted(final_scores.items(),
                   key=lambda x: x[1]['score'],
                   reverse=True)[:top_n]
    
    # Step 5: Display results
    print(f"\n🏥 TOP {top_n} DIAGNOSES:")
    print(f"{'─'*50}")
    
    results = []
    for rank, (disease, info) in enumerate(ranked, 1):
        # Get precautions
        precautions = [n for n in G.successors(disease)
                      if G.nodes[n].get('node_type') == 'Precaution']
        
        # Get description
        description = G.nodes[disease].get('description', 
                                           'No description available')
        
        print(f"\n#{rank} {disease}")
        print(f"   Score:     {info['score']:.3f}")
        print(f"   Coverage:  {info['coverage']*100:.1f}% "
              f"({info['matched_count']}/{info['total_symptoms']} symptoms)")
        print(f"   Matched:   {', '.join(info['matched_symptoms'])}")
        print(f"   Precautions: {', '.join(precautions[:3])}")
        
        results.append({
            'rank': rank,
            'disease': disease,
            'score': info['score'],
            'coverage': info['coverage'],
            'matched_symptoms': info['matched_symptoms'],
            'precautions': precautions,
            'description': description
        })
    
    return results           
# %% TEST THE ENGINE
# ============================================================
#%%
# Test 1 — Common Cold symptoms
results1 = diagnose(
    "patient has continuous sneezing, runny nose and mild fever"
)

#%%
# Test 2 — Malaria symptoms  
results2 = diagnose(
    "high fever, chills, sweating and headache"
)

#%%
# Test 3 — Diabetes symptoms
results3 = diagnose( "increased thirst, frequent urination and fatigue")
#%% LLM Layer
import anthropic
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    _env_path = Path(__file__).resolve().parent / '.env'
except NameError:
    # __file__ is not defined in VS Code Python Interactive (#%%) mode
    _env_path = Path.cwd() / '.env'

load_dotenv(_env_path)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def llm_explain_diagnosis(query_text,diagnosis_results):
   '''
    Takes diagnosis results from graph engine
    Returns clinical explanation from LLM
    
    Input:  raw graph traversal results
    Output: doctor-friendly clinical narrative
    '''
   if not diagnosis_results:
       return "Unable to generate explanation — no diagnoses found."
   
   #Structured context for LLMs
   #pass graph results as context
   
   diagnoses_text = ""
   for result in diagnosis_results:
       diagnoses_text += f"""Rank #{result['rank']}: {result['disease']}
            - Confidence Score: {result['score']:.3f}
            - Symptom Coverage: {result['coverage']*100:.1f}%
            - Matched Symptoms: {', '.join(result['matched_symptoms'])}
            - Disease Description: {result['description']}
            - Recommended Precautions: {', '.join(result['precautions'][:4])}
            """
   prompt = f"""You are an experienced medical AI assistant helping doctors with differential diagnosis.

    PATIENT COMPLAINT:
    {query_text}

    KNOWLEDGE GRAPH ANALYSIS:
    {diagnoses_text}

    Based on the knowledge graph analysis above, provide:

    1. PRIMARY DIAGNOSIS: Explain why the top-ranked disease 
    is most likely, referencing specific matched symptoms

    2. DIFFERENTIAL DIAGNOSES: Briefly explain other 
    possibilities and how to distinguish them

    3. RED FLAGS: Any symptoms that warrant immediate attention

    4. RECOMMENDED NEXT STEPS: Tests or actions to confirm 
    diagnosis

    Keep response concise, clinical, and actionable.
    Important: Base your reasoning ONLY on the knowledge 
    graph data provided above — do not add diseases or 
    symptoms not in the analysis.

    DISCLAIMER: This is a decision support tool only. 
    Final diagnosis must be made by a qualified physician."""
                    
   message  = client.messages.create(model="claude-sonnet-4-5",max_tokens=1000,messages=[{"role":"user","content": prompt}])
   return message.content[0].text

def full_diagnosis_pipeline(text,top_n=3):
    """Complete pipeline: Free text -> Grpah reasoning -> LLM explanation"""
    print(f"\n{'='*55}")
    print(f" MEDICAL DIAGNOSIS ASSISTANT")
    print(f"{'='*55}")
    # Step 1: Graph-based diagnosis
    print("\n Running Knowledge Graph Analysis...")
    results = diagnose(text, top_n=top_n)
    if not results:
        return "No diagnosis possible with given symptoms."
    # Step 2: LLM explanation
    print("\n Generating Clinical Explanation...")
    explanation = llm_explain_diagnosis(text, results)
    print(f"\n{'='*55}")
    print(f"📋 CLINICAL REPORT")
    print(f"{'='*55}")
    print(explanation)
    print(f"\n{'─'*55}")
    print("⚠️  DISCLAIMER: AI-assisted decision support only.")
    print("    Final diagnosis by qualified physician only.")
    print(f"{'─'*55}")
    
    return {
        'query': text,
        'graph_results': results,
        'llm_explanation': explanation
    }
#%%
report1 = full_diagnosis_pipeline(
    "patient has high fever, chills, sweating and headache"
)
# %%
print("\n" + "="*55)
print("LLM CLINICAL EXPLANATION:")
print("="*55)
print(report1['llm_explanation'])
# %%
