import os
import json
import requests
import base64

# HELPER: Get deployment name from env or default to gpt-4o
DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT_NAME", "gpt-4o")

def find_prerequisite(topic, db_driver):
    query = """
    MATCH (m:MicroSkill {name: $topic})-[:REQUIRES_PREREQUISITE]->(p:MicroSkill)
    RETURN p.name AS prereq LIMIT 1
    """
    with db_driver.session() as session:
        result = session.run(query, topic=topic)
        record = result.single()
        return record["prereq"] if record else None

def generate_draft_script(student_name, grade, topic, prereq, interest, ai_client):
    scaffold = f"Connect '{topic}' to prior knowledge of '{prereq}'." if prereq else ""
    prompt = f"You are Ananya, an elite AI tutor. Student: {student_name}, Grade: {grade}. Topic: '{topic}'. Interest: '{interest}'. {scaffold} STRICT GUARDRAILS: ONLY teach Grade {grade} concepts. Write a 3-sentence spoken script. NO MARKDOWN."
    
    # Updated for Azure Deployment compatibility
    res = ai_client.chat.completions.create(
        model=DEPLOYMENT, 
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.replace('*', '')

def shadow_student_veto(script, grade, interest, ai_client):
    prompt = f"You are a distracted {grade}yr old obsessed with {interest}. Read: '{script}'. Is it boring? Return ONLY JSON: {{"approved": true, "feedback": "reason"}}"
    res = ai_client.chat.completions.create(
        model=DEPLOYMENT, 
        messages=[{"role": "user", "content": prompt}], 
        response_format={"type":"json_object"}
    )
    return json.loads(res.choices[0].message.content)

def rewrite_script(script, grade, interest, feedback, ai_client):
    prompt = f"Rewrite for a {grade}yr old. Feedback: {feedback}. Script: {script}"
    res = ai_client.chat.completions.create(
        model=DEPLOYMENT, 
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.replace('*', '')

def generate_visual_payload(script, ai_client):
    prompt = f"Design JSON visual payload (visual_type, screen_elements, animation_action) for: {script}"
    res = ai_client.chat.completions.create(
        model=DEPLOYMENT, 
        messages=[{"role": "user", "content": prompt}], 
        response_format={"type":"json_object"}
    )
    return json.loads(res.choices[0].message.content)

def generate_audio_base64(script):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
    data = {"text": script, "model_id": "eleven_multilingual_v2"}
    req = requests.post(url, json=data, headers=headers)
    if req.status_code == 200:
        return base64.b64encode(req.content).decode()
    return None

def update_graph_memory(topic, db_driver):
    query = "MATCH (m:MicroSkill {name: $topic}) SET m.elo_rating = coalesce(m.elo_rating, 1200) + 10 RETURN m.elo_rating"
    with db_driver.session() as session:
        session.run(query, topic=topic)
