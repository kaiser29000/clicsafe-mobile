import streamlit as st
import time
import pandas as pd
import plotly.express as px
from twilio.rest import Client
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="ClicSafe", page_icon="🛡️", layout="centered")

# --- MÉMOIRE DE L'APPLICATION (Session State) ---
if 'contacts' not in st.session_state:
    st.session_state['contacts'] = ["", "", ""]
if 'twilio_sid' not in st.session_state:
    st.session_state['twilio_sid'] = ""
if 'twilio_token' not in st.session_state:
    st.session_state['twilio_token'] = ""
if 'twilio_number' not in st.session_state:
    st.session_state['twilio_number'] = ""
if 'latitude' not in st.session_state:
    st.session_state['latitude'] = None
if 'longitude' not in st.session_state:
    st.session_state['longitude'] = None

# --- BOUTON D'URGENCE (Quitter vite) ---
col1, col2 = st.columns([3, 1])
with col2:
    st.link_button("⚠️ QUITTER VITE", "https://www.google.fr", type="primary", use_container_width=True)

st.title("🛡️ ClicSafe")
st.markdown("*Votre position et votre alerte envoyées en un clic.*")

tab1, tab2, tab3 = st.tabs(["🚨 ALERTE", "📍 MA POSITION", "⚙️ RÉGLAGES"])

# ---------------------------------------------------------
# ONGLET 1 : L'ALERTE (Envoi du vrai SMS)
# ---------------------------------------------------------
with tab1:
    st.subheader("Situation actuelle")
    type_danger = st.radio(
        "Motif :",
        ["🤫 Je me sens suivi(e)", "🏠 Violence domestique", "🥊 Agression", "🩺 Urgence médicale"],
        label_visibility="collapsed"
    )
    
    # Message de prévention si le GPS n'est pas activé
    if st.session_state['latitude'] is None:
        st.warning("⚠️ Attention : Votre position GPS n'a pas encore été récupérée. Allez dans l'onglet '📍 MA POSITION' avant d'envoyer l'alerte pour plus de précision.")
    else:
        st.success(f"✅ GPS Verrouillé : {st.session_state['latitude']}, {st.session_state['longitude']}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚨 ENVOYER L'ALERTE SMS", use_container_width=True, type="primary"):
        contacts_valides = [c for c in st.session_state['contacts'] if c != ""]
        
        if not contacts_valides:
            st.error("❌ Aucun contact enregistré dans les réglages.")
        elif not st.session_state['twilio_sid'] or not st.session_state['twilio_token']:
            st.error("❌ Les clés d'API Twilio ne sont pas configurées dans les réglages. Impossible d'envoyer un vrai SMS.")
        else:
            with st.spinner("Transmission de l'alerte via le réseau mobile..."):
                try:
                    # Connexion à l'API Twilio
                    client = Client(st.session_state['twilio_sid'], st.session_state['twilio_token'])
                    
                    # Préparation du lien Google Maps
                    lien_maps = "Position inconnue"
                    if st.session_state['latitude']:
                        lien_maps = f"https://www.google.com/maps/search/?api=1&query={st.session_state['latitude']},{st.session_state['longitude']}"
                    
                    # Le texte exact du SMS
                    message_sms = f"ALERTE CLICSAFE 🚨\nMotif : {type_danger}\nLocalisation : {lien_maps}\nContactez-moi ou appelez les secours."
                    
                    # Envoi à chaque contact
                    sms_envoyes = 0
                    for numero in contacts_valides:
                        message = client.messages.create(
                            body=message_sms,
                            from_=st.session_state['twilio_number'],
                            to=numero
                        )
                        sms_envoyes += 1
                        
                    st.success(f"✅ VRAIE ALERTE ENVOYÉE à {sms_envoyes} contact(s) !")
                    st.info("Le SMS reçu par vos proches contient un lien direct vers Google Maps avec votre position.")
                except Exception as e:
                    st.error(f"❌ Erreur d'envoi Twilio : {e}")
                    st.markdown("*Avez-vous bien vérifié ce numéro sur votre compte Twilio gratuit ?*")

# ---------------------------------------------------------
# ONGLET 2 : LA CARTE ET LE GPS
# ---------------------------------------------------------
with tab2:
    st.subheader("Votre localisation")
    st.markdown("Cliquez sur le bouton ci-dessous pour autoriser l'application à lire votre puce GPS.")
    
    # Le composant qui va chercher le GPS du navigateur
    localisation = streamlit_geolocation()
    
    if localisation['latitude'] is not None and localisation['longitude'] is not None:
        st.session_state['latitude'] = localisation['latitude']
        st.session_state['longitude'] = localisation['longitude']
        
    if st.session_state['latitude'] is not None:
        st.success("✅ Position acquise avec succès.")
        
        # Création de la carte avec Plotly
        df_gps = pd.DataFrame({'lat': [st.session_state['latitude']], 'lon': [st.session_state['longitude']]})
        fig = px.scatter_mapbox(
            df_gps, lat="lat", lon="lon", 
            color_discrete_sequence=["red"], size_max=15, zoom=14, mapbox_style="carto-positron"
        )
        # On force la taille du point
        fig.update_traces(marker=dict(size=15))
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("En attente de la localisation... Si rien ne se passe, vérifiez que vous avez autorisé le GPS dans votre navigateur.")

# ---------------------------------------------------------
# ONGLET 3 : LES RÉGLAGES (Connexion Twilio)
# ---------------------------------------------------------
with tab3:
    st.subheader("1. Moteur SMS (API Twilio)")
    st.markdown("Pour envoyer de vrais SMS, vous devez créer un compte sur [Twilio.com](https://www.twilio.com) et récupérer vos clés gratuites.")
    
    # type="password" cache les clés pour la sécurité
    sid = st.text_input("Account SID Twilio", value=st.session_state['twilio_sid'], type="password")
    token = st.text_input("Auth Token Twilio", value=st.session_state['twilio_token'], type="password")
    tw_num = st.text_input("Votre numéro Twilio (ex: +123456789)", value=st.session_state['twilio_number'])
    
    st.divider()
    
    st.subheader("2. Mes Contacts de Confiance")
    st.markdown("⚠️ *Important : Avec un compte Twilio gratuit, ces numéros doivent avoir été vérifiés au préalable sur votre console Twilio.*")
    c1 = st.text_input("📞 Contact n°1 (Format International, ex: +33612345678)", value=st.session_state['contacts'][0])
    c2 = st.text_input("📞 Contact n°2", value=st.session_state['contacts'][1])
    c3 = st.text_input("📞 Contact n°3", value=st.session_state['contacts'][2])
    
    if st.button("💾 Sauvegarder la configuration globale"):
        st.session_state['twilio_sid'] = sid
        st.session_state['twilio_token'] = token
        st.session_state['twilio_number'] = tw_num
        st.session_state['contacts'] = [c1, c2, c3]
        st.success("Système paramétré et armé !")