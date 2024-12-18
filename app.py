import streamlit as st
import requests
import time
import json
import base64
from PIL import Image
from io import BytesIO
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
ENDPOINT_URL = os.getenv('ENDPOINT_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Test OpenAI connection
try:
    test_response = client.chat.completions.create(
        messages=[{"role": "user", "content": "test"}],
        model="gpt-4o",
        max_tokens=5
    )
    print("OpenAI API connection successful")
except Exception as e:
    print(f"OpenAI API connection failed: {str(e)}")

def generate_image(prompt):
    # Prepare the headers and payload
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "prompt": str(prompt),
            "negative_prompt": "brutto, sfocato, bassa qualità, nsfw, nudo, contenuto esplicito, " +
                             "violenza, sangue, gore, inquietante, spaventoso, contenuto inappropriato",
        }
    }
    
    try:
        # Submit the generation request
        response = requests.post(ENDPOINT_URL, headers=headers, json=payload)
        if response.status_code != 200:
            return None, f"Error: {response.status_code} - {response.text}"
        
        job_id = response.json()["id"]
        
        # Poll for results
        status_url = f"https://api.runpod.ai/v2/kbrj7vlrl28jyo/status/{job_id}"
        with st.spinner('Generating your image...'):
            while True:
                response = requests.get(status_url, headers=headers)
                status_data = response.json()
                
                if status_data["status"] == "COMPLETED":
                    data_url = status_data["output"]["image_url"]
                    base64_image = data_url.split(',')[1]
                    image_bytes = base64.b64decode(base64_image)
                    image = Image.open(BytesIO(image_bytes))
                    return image, None
                
                elif status_data["status"] == "FAILED":
                    error_msg = status_data.get('error', 'Unknown error')
                    print(f"Generation failed with error: {error_msg}")
                    return None, f"Generation failed: {error_msg}"
                
                time.sleep(2)
    except Exception as e:
        print(f"Exception in generate_image: {str(e)}")
        return None, f"Error during image generation: {str(e)}"

def contains_inappropriate_content(text):
    """Check if the prompt contains inappropriate content in Italian or English"""
    inappropriate_terms = {
        # Inappropriate content categories
        'violenza': [
            'violenza', 'sangue', 'morte', 'uccidere', 'tortura', 'mutilazione',
            'violento', 'violenta', 'armi', 'guerra'
        ],
        'contenuto_esplicito': [
            'nudo', 'nuda', 'nudità', 'erotico', 'erotica', 'sensuale',
            'sexy', 'provocante', 'provocanti', 'intimo', 'intima',
            'bikini', 'lingerie'
        ],
        'contenuto_offensivo': [
            'razzista', 'razzismo', 'discriminazione', 'offensivo', 'offensiva',
            'insulto', 'insulti', 'odio', 'pregiudizio'
        ],
        # Common English terms to block as well
        'english_inappropriate': [
            'nude', 'naked', 'nsfw', 'explicit', 'adult', 'sexy',
            'violence', 'gore', 'blood', 'death', 'kill'
        ]
    }
    
    # Convert text to lowercase for case-insensitive matching
    text = text.lower()
    
    # Check each category
    found_terms = []
    for category, terms in inappropriate_terms.items():
        for term in terms:
            if term in text:
                found_terms.append(term)
    
    return bool(found_terms), found_terms

def check_content_with_chatgpt(prompt):
    """Use ChatGPT to determine if the content is appropriate"""
    try:
        print("Sending request to OpenAI...")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": """You are a content moderator. 
                Analyze the following prompt for inappropriate content including:
                - Violence or gore
                - Adult or explicit content
                - Hate speech or discrimination
                - Dangerous or illegal activities
                Respond with only 'safe' or 'unsafe' followed by a brief reason if unsafe."""},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o",
            temperature=0,
            max_tokens=50
        )
        result = response.choices[0].message.content.lower()
        print(f"OpenAI response: {result}")
        is_safe = result.startswith('safe')
        reason = result.split('unsafe:')[-1].strip() if not is_safe else None
        return is_safe, reason
    except Exception as e:
        print(f"Error in OpenAI call: {str(e)}")
        return True, None  # Default to safe if API call fails

# Set page config
st.set_page_config(page_title="Generatore di Immagini AI", page_icon="🎨")

# Title and description
st.title("🎨 Generatore di Immagini AI")
st.markdown("Crea immagini straordinarie da descrizioni testuali utilizzando tecnologia AI avanzata.")

# Add this after the title and before the main controls
st.markdown("---")

# Main controls
st.header("Crea la Tua Immagine")
prompt = st.text_area(
    "Il tuo Prompt",
    placeholder="Un maestoso castello su un'isola fluttuante al tramonto, con draghi che volano intorno...",
    height=100
)

if st.button("🚀 Genera Immagine", type="primary", use_container_width=True):
    if not prompt:
        st.error("Per favore, inserisci prima una descrizione!")
    else:
        # First check with basic filter
        is_inappropriate, found_terms = contains_inappropriate_content(prompt)
        if is_inappropriate:
            st.error("⚠️ La tua richiesta contiene contenuti non appropriati. " +
                    "Per favore, modifica la descrizione e riprova.")
            st.warning("Mantieni le descrizioni appropriate per tutti.")
        else:
            # Then check with ChatGPT
            is_safe, reason = check_content_with_chatgpt(prompt)
            if not is_safe:
                st.error(f"⚠️ La tua richiesta è stata identificata come inappropriata.")
                st.warning("Mantieni le descrizioni appropriate per tutti.")
            else:
                image, error = generate_image(prompt)
                if error:
                    st.error(error)
                elif image:
                    st.session_state.generated_image = image
                    st.session_state.show_tips = False

# Tips and Notes without columns
with st.expander("💡 Suggerimenti per risultati migliori", expanded=True):
    st.markdown("""
    - Sii specifico su quello che vuoi vedere
    - Includi dettagli su stile, illuminazione e atmosfera
    - Usa aggettivi descrittivi come "vibrante", "cupo" o "etereo"
    - Menziona stili artistici: "dipinto ad olio", "arte digitale", "acquerello"
    """)

with st.expander("⚠️ Note Importanti", expanded=True):
    st.markdown("""
    - La generazione richiede tipicamente 30-60 secondi
    - Mantieni le descrizioni appropriate per tutti
    """)

# Image display area
st.markdown("### Il Tuo Capolavoro")
if 'generated_image' in st.session_state:
    st.image(st.session_state.generated_image, use_container_width=True)
    # Add download button
    buf = BytesIO()
    st.session_state.generated_image.save(buf, format="PNG")
    st.download_button(
        label="📥 Scarica Immagine",
        data=buf.getvalue(),
        file_name="immagine_generata.png",
        mime="image/png",
        use_container_width=True
    )
else:
    st.info("La tua immagine generata apparirà qui")

# Footer
st.markdown("---")
