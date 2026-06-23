import streamlit as st
import anthropic
import networkx as nx
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import os

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Medical Diagnosis Assistant",
    page_icon="🏥",
    layout="wide"
)

# ============================================================
# LOAD DATA & BUILD GRAPH (cached — runs once)
# ============================================================
@st.cache_resource
def load_knowledge_graph():
    '''Load data and build graph once — cache for speed'''
    
    # Load datasets
    df_dataset     = pd.read_csv('dataset.csv')
    df_description = pd.read_csv('symptom_Description.csv')
    df_precaution  = pd.read_csv('symptom_precaution.csv')
    df_severity    = pd.read_csv('Symptom-severity.csv')
    
    # Wide to long
    symptom_cols = [c for c in df_dataset.columns 
                    if c != 'Disease']
    df_long = df_dataset.melt(
        id_vars=['Disease'],
        value_vars=symptom_cols,
        var_name='Position',
        value_name='Symptom'
    )
    df_long = df_long.dropna(subset=['Symptom'])
    df_long = df_long[df_long['Symptom'].str.strip() != '']
    df_long = df_long.drop('Position', axis=1)
    df_long['Symptom'] = df_long['Symptom'].str.strip()
    df_long['Disease'] = df_long['Disease'].str.strip()
    df_long = df_long.drop_duplicates()
    
    # Add severity
    df_severity.columns = df_severity.columns.str.strip()
    df_severity['Symptom'] = df_severity['Symptom'].str.strip()
    df_edges = pd.merge(df_long, df_severity, 
                        on='Symptom', how='left')
    df_edges['weight'] = df_edges['weight'].fillna(
                         df_edges['weight'].median())
    
    # Build graph
    G = nx.DiGraph()
    
    # Disease nodes
    for _, row in df_description.iterrows():
        disease = row['Disease'].strip()
        desc    = row['Description'].strip() \
                  if 'Description' in row else ''
        G.add_node(disease, node_type='Disease', 
                   description=desc)
    
    # Symptom nodes
    for symptom in df_edges['Symptom'].unique():
        sev = df_severity[
            df_severity['Symptom']==symptom]['weight'].values
        sev = float(sev[0]) if len(sev) > 0 else 3.0
        G.add_node(symptom, node_type='Symptom', severity=sev)
    
    # INDICATES edges
    for _, row in df_edges.iterrows():
        G.add_edge(row['Symptom'], row['Disease'],
                   relationship='INDICATES',
                   weight=float(row['weight']))
    
    # PRECAUTION edges
    prec_cols = [c for c in df_precaution.columns 
                 if c != 'Disease']
    for _, row in df_precaution.iterrows():
        disease = row['Disease'].strip()
        for col in prec_cols:
            if pd.notna(row[col]) and str(row[col]).strip():
                prec = str(row[col]).strip()
                if not G.has_node(prec):
                    G.add_node(prec, node_type='Precaution')
                G.add_edge(disease, prec, 
                          relationship='PRECAUTION')
    
    return G

# ============================================================
# DIAGNOSIS FUNCTIONS (same as before)
# ============================================================
def fuzzy_match_symptom(G, input_term, threshold=0.6):
    symptom_nodes = [n for n, d in G.nodes(data=True)
                     if d.get('node_type') == 'Symptom']
    input_clean = input_term.lower().strip().replace(' ','_')
    best_match, best_score = None, 0
    
    for symptom in symptom_nodes:
        symptom_clean = symptom.lower().strip()
        if input_clean == symptom_clean:
            return symptom, 1.0
        if input_clean in symptom_clean:
            score = len(input_clean) / len(symptom_clean)
            if score > best_score:
                best_score, best_match = score, symptom
            continue
        score = SequenceMatcher(
            None, input_clean, symptom_clean).ratio()
        if score > best_score:
            best_score, best_match = score, symptom
    
    return (best_match, best_score) \
           if best_score >= threshold else (None, 0)

def extract_symptoms(G, text):
    symptom_nodes = [n.lower().replace('_',' ')
                     for n, d in G.nodes(data=True)
                     if d.get('node_type') == 'Symptom']
    text_clean = text.lower().replace(',',' ').replace('.',' ')
    stop_words = ['patient','has','have','with','and','the',
                  'a','an','mild','severe','chronic','acute',
                  'persistent','slight','some','feeling']
    matched, matched_names = [], set()
    
    for symptom in sorted(symptom_nodes, 
                          key=len, reverse=True):
        if symptom in text_clean:
            canonical = symptom.replace(' ','_')
            nodes = [n for n in G.nodes()
                    if n.lower()==canonical.lower()
                    or n.lower()==symptom.lower()]
            if nodes and nodes[0] not in matched_names:
                matched.append((nodes[0], 1.0))
                matched_names.add(nodes[0])
                text_clean = text_clean.replace(symptom,' ')
    
    remaining = [w for w in text_clean.split()
                if w not in stop_words and len(w) > 3]
    for word in remaining:
        match, score = fuzzy_match_symptom(G, word, 0.65)
        if match and match not in matched_names:
            matched.append((match, score))
            matched_names.add(match)
    
    return matched

def diagnose_graph(G, text, top_n=3):
    matched_symptoms = extract_symptoms(G, text)
    if not matched_symptoms:
        return [], []
    
    disease_scores, disease_syms = {}, {}
    for symptom, match_score in matched_symptoms:
        if symptom not in G.nodes():
            continue
        for disease in G.successors(symptom):
            if G.nodes[disease].get('node_type') != 'Disease':
                continue
            weight = G.get_edge_data(
                symptom, disease).get('weight', 3)
            if disease not in disease_scores:
                disease_scores[disease] = 0
                disease_syms[disease]   = []
            disease_scores[disease] += weight * match_score
            disease_syms[disease].append(symptom)
    
    final = {}
    for disease, score in disease_scores.items():
        total = len([n for n in G.predecessors(disease)
                    if G.nodes[n].get('node_type')=='Symptom'])
        matched  = len(disease_syms[disease])
        coverage = matched/total if total > 0 else 0
        precs    = [n for n in G.successors(disease)
                   if G.nodes[n].get('node_type')=='Precaution']
        desc     = G.nodes[disease].get('description','')
        
        final[disease] = {
            'score':            score * coverage,
            'coverage':         coverage,
            'matched_symptoms': disease_syms[disease],
            'total_symptoms':   total,
            'matched_count':    matched,
            'precautions':      precs,
            'description':      desc
        }
    
    ranked = sorted(final.items(),
                   key=lambda x: x[1]['score'],
                   reverse=True)[:top_n]
    
    return matched_symptoms, ranked

def get_llm_explanation(client, query, ranked_results):
    diagnoses_text = ""
    for rank, (disease, info) in enumerate(ranked_results, 1):
        diagnoses_text += f"""
Rank #{rank}: {disease}
- Score: {info['score']:.3f}
- Coverage: {info['coverage']*100:.1f}%
- Matched Symptoms: {', '.join(info['matched_symptoms'])}
- Description: {info['description']}
- Precautions: {', '.join(info['precautions'][:4])}
"""
    
    prompt = f"""You are an experienced medical AI assistant.

PATIENT COMPLAINT: {query}

KNOWLEDGE GRAPH ANALYSIS:
{diagnoses_text}

Provide a concise clinical report with:
1. PRIMARY DIAGNOSIS — why most likely
2. DIFFERENTIAL DIAGNOSES — how to distinguish
3. RED FLAGS — urgent symptoms to watch
4. NEXT STEPS — tests to confirm

Base reasoning ONLY on graph data provided.
Keep response clear and actionable."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# ============================================================
# STREAMLIT UI
# ============================================================
def main():
    # Header
    st.title("🏥 Medical Diagnosis Assistant")
    st.markdown("**Graph RAG powered clinical decision support**")
    st.warning("⚠️ For educational purposes only. "
               "Always consult a qualified physician.")
    
    # Load graph
    with st.spinner("Loading Medical Knowledge Graph..."):
        G = load_knowledge_graph()
    
    # Graph stats in sidebar
    st.sidebar.title("📊 Knowledge Graph Stats")
    node_types = {}
    for _, d in G.nodes(data=True):
        t = d.get('node_type', 'Unknown')
        node_types[t] = node_types.get(t, 0) + 1
    
    st.sidebar.metric("Total Nodes", G.number_of_nodes())
    st.sidebar.metric("Total Edges", G.number_of_edges())
    for ntype, count in node_types.items():
        st.sidebar.metric(f"{ntype} Nodes", count)
    
    # API Key input
    st.sidebar.title("🔑 API Settings")
    api_key = st.sidebar.text_input(
        "Anthropic API Key",
        type="password",
        help="Enter your Anthropic API key"
    )
    
    # Main input
    st.subheader("📝 Describe Patient Symptoms")
    
    # Example buttons
    st.markdown("**Quick examples:**")
    col1, col2, col3 = st.columns(3)
    
    example_text = ""
    with col1:
        if st.button("🦟 Malaria symptoms"):
            example_text = "high fever, chills, sweating and headache"
    with col2:
        if st.button("🤧 Cold symptoms"):
            example_text = "continuous sneezing, runny nose and mild fever"
    with col3:
        if st.button("💉 Diabetes symptoms"):
            example_text = "increased thirst, frequent urination and fatigue"
    
    # Text input
    symptom_text = st.text_area(
        "Enter symptoms in plain English:",
        value=example_text,
        height=100,
        placeholder="e.g. patient has high fever, chills and headache..."
    )
    
    # Diagnose button
    if st.button("🔍 Analyze Symptoms", type="primary"):
        if not symptom_text.strip():
            st.error("Please enter symptoms first.")
            return
        
        # Graph analysis
        with st.spinner("Analyzing symptoms in Knowledge Graph..."):
            matched_symptoms, ranked = diagnose_graph(
                G, symptom_text)
        
        if not matched_symptoms:
            st.error("No symptoms matched. "
                    "Try different symptom descriptions.")
            return
        
        # Display matched symptoms
        st.subheader("✅ Identified Symptoms")
        sym_cols = st.columns(len(matched_symptoms))
        for i, (sym, score) in enumerate(matched_symptoms):
            severity = G.nodes[sym].get('severity', 3)
            with sym_cols[i]:
                st.metric(
                    label=sym.replace('_',' ').title(),
                    value=f"Severity: {severity}",
                    delta=f"Match: {score:.0%}"
                )
        
        # Display diagnoses
        st.subheader("🏥 Differential Diagnoses")
        
        colors = ['🥇', '🥈', '🥉']
        for rank, (disease, info) in enumerate(ranked):
            with st.expander(
                f"{colors[rank]} #{rank+1} {disease} "
                f"— Coverage: {info['coverage']*100:.1f}%",
                expanded=(rank==0)
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Confidence Score", 
                             f"{info['score']:.3f}")
                    st.metric("Symptom Coverage",
                             f"{info['matched_count']}"
                             f"/{info['total_symptoms']}")
                    st.markdown("**Matched Symptoms:**")
                    for sym in info['matched_symptoms']:
                        st.markdown(f"• {sym.replace('_',' ')}")
                
                with col2:
                    st.markdown("**Recommended Precautions:**")
                    for prec in info['precautions'][:5]:
                        st.markdown(f"• {prec}")
                
                if info['description']:
                    st.info(f"📚 {info['description']}")
        
        # LLM Explanation
        if api_key:
            st.subheader("🤖 AI Clinical Explanation")
            with st.spinner("Generating clinical report..."):
                try:
                    client = anthropic.Anthropic(
                        api_key=api_key)
                    explanation = get_llm_explanation(
                        client, symptom_text, ranked)
                    st.markdown(explanation)
                except Exception as e:
                    st.error(f"LLM Error: {str(e)}")
        else:
            st.info("💡 Add Anthropic API key in sidebar "
                   "for AI clinical explanation")
        
        # Graph visualization
        st.subheader("🕸️ Knowledge Graph View")
        if ranked:
            top_disease = ranked[0][0]
            sym_nodes   = [n for n in G.predecessors(top_disease)
                          if G.nodes[n].get('node_type')=='Symptom']
            prec_nodes  = [n for n in G.successors(top_disease)
                          if G.nodes[n].get('node_type')=='Precaution']
            
            import matplotlib.pyplot as plt
            subgraph = G.subgraph(
                [top_disease] + sym_nodes + prec_nodes)
            
            colors = []
            for node in subgraph.nodes():
                ntype = G.nodes[node].get('node_type')
                if ntype == 'Disease':    colors.append('red')
                elif ntype == 'Symptom':  colors.append('steelblue')
                else:                     colors.append('green')
            
            fig, ax = plt.subplots(figsize=(12, 6))
            pos = nx.spring_layout(subgraph, seed=42)
            nx.draw_networkx(subgraph, pos,
                           node_color=colors,
                           node_size=1500,
                           font_size=7,
                           arrows=True,
                           ax=ax)
            ax.axis('off')
            ax.set_title(f"Knowledge Graph — {top_disease}")
            st.pyplot(fig)

if __name__ == "__main__":
    main()