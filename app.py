import streamlit as st
import os
from neo4j import GraphDatabase
from openai import AzureOpenAI
import cognitive_engine as brain

@st.cache_resource
def init_connections():
    driver = GraphDatabase.driver(os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]))
    client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"], api_key=os.environ["AZURE_OPENAI_KEY"], api_version="2024-02-15-preview")
    return driver, client

db_driver, ai_client = init_connections()

st.set_page_config(page_title="Math Foundry OS", layout="centered")
st.title("🧠 Math Foundry: Ananya")

col1, col2 = st.columns(2)
with col1:
    student_name = st.text_input("Student Name", placeholder="e.g., Amit")
    selected_grade = st.selectbox("Select Grade", options=[3, 4, 5, 6, 7, 8, 9, 10])

def get_live_topics(grade):
    with db_driver.session() as session:
        res = session.run("MATCH (m:MicroSkill)-[:BELONGS_TO]->(g:GradeLevel {level: $grade}) RETURN m.name", grade=grade)
        return [r["m.name"] for r in res] or ["No topics found."]

live_topics = get_live_topics(selected_grade)
with col2:
    selected_topic = st.selectbox("Select Starting Topic", options=live_topics)
    interest = st.text_input("Current Obsession", placeholder="e.g., Hunk of Junk Monster")

if st.button("🚀 Start Lesson", use_container_width=True):
    if student_name and selected_topic:
        with st.status("Initializing Cognitive OS...", expanded=True) as status:
            prereq = brain.find_prerequisite(selected_topic, db_driver)
            draft = brain.generate_draft_script(student_name, selected_grade, selected_topic, prereq, interest, ai_client)
            veto = brain.shadow_student_veto(draft, selected_grade, interest, ai_client)
            final_script = brain.rewrite_script(draft, selected_grade, interest, veto.get('feedback'), ai_client) if not veto.get("approved") else draft
            visuals = brain.generate_visual_payload(final_script, ai_client)
            b64_audio = brain.generate_audio_base64(final_script)
            brain.update_graph_memory(selected_topic, db_driver)
            status.update(label="Lesson Ready!", state="complete", expanded=False)

        if b64_audio: st.markdown(f'<audio autoplay controls src="data:audio/mpeg;base64,{b64_audio}"></audio>', unsafe_allow_html=True)
        st.json(visuals)
        st.write(final_script)
