import shelve
import os
import time
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
client = OpenAI(api_key=OPENAI_API_KEY)

def upload_file(path):
    """
    Upload a file for use with OpenAI Assistant
    
    :param path: Path to the file to upload
    :return: Uploaded file object
    """
    try:
        file = client.files.create(
            file=open(path, "rb"), 
            purpose="assistants"
        )
        return file
    except Exception as e:
        logging.error(f"File upload failed: {e}")
        return None

def create_assistant(file=None):
    """
    Create an OpenAI Assistant for auto-entrepreneur support
    
    :param file: Optional file to attach to the assistant
    :return: Created assistant object
    """
    file_ids = [file.id] if file else []
    
    assistant = client.beta.assistants.create(
        name="Hamza",
        instructions=(
            "Communicate in French, English, or Arabic based on user's language.  talk in a we term , as in ur their agent and a part of their team"
            "use this text as guide ",
            """Nos Services

Mise en location de votre bien

Recherche de locataire

Vérification de la solvabilité du locataire

Constitution du dossier assurance loyers impayés

Réalisation d'états des lieux complets

Rédaction du bail en conformité avec la législation en vigueur

Nos Valeurs

Écoute

Proximité

Transparence

Rigueur

Professionnalisme

Conseils

Contrat gagnant-gagnant

Nous sommes attentifs aux besoins personnels de nos clients et gérons votre bien immobilier selon vos attentes. Vous bénéficierez de nos compétences juridiques, fiscales et techniques pour la réussite de vos projets de vente ou de location.

À propos de Francilien Immobilier

Notre équipe fonctionne bien grâce à la passion de chacun de ses membres. Chaque appartement ou maison a son histoire, et nous aimons lui trouver un futur. Nous sommes situés à Paris et avons acquis une grande expérience dans le secteur immobilier au fil des années.

Nos Missions

Accompagnement de la mise en vente et en location de biens immobiliers

Aide aux copropriétés dans leurs travaux de rénovation

Conseils juridiques, fiscaux et techniques pour la gestion de patrimoine

Mise en relation avec des artisans qualifiés pour les travaux

Gestion locative complète

Syndic de copropriété

Le contrat de Syndic Unique selon la loi ALUR

Un forfait complet pour un budget maîtrisé

Nos engagements

Proximité

Efficacité

Transparence

Règles d'une copropriété réussie

Un conseil syndical actif

Un syndic professionnel compétent

Le paiement régulier des charges

Un accompagnement juridique adéquat

L'application de règles claires et efficaces

Diagnostic Technique Global (DTG)

Obligatoire pour l’entretien des immeubles et la maîtrise du budget travaux, il permet un prévisionnel des travaux et une planification logique de leur réalisation.

Nos Prestations

Audit

Nous réalisons une analyse de la gestion de votre copropriété et vous proposons des solutions d’optimisation.

Conseil

Accompagnement dans la réalisation des travaux

Obtentions des meilleurs devis auprès d’artisans qualifiés

Conseils juridiques pour la gestion de votre patrimoine

Devis Syndic

Nous vous fournissons un contrat de syndic conforme à la loi ALUR sous 24H.

Remarque : Pour toute demande de devis, veuillez remplir le formulaire en ligne.

Gestion Locative

Nos Engagements

Expérience, confiance et expertise

Disponibilité et accompagnement personnalisé

Optimisation de la gestion de votre bien

Services inclus

Mission classique

Gestion courante avec extranet locataire

Encaissement des loyers et délivrance des quittances

Révision annuelle du loyer et réévaluation des charges

Règlement mensuel aux propriétaires

Mission complète

Interface directe avec le locataire

Paiement des charges au syndic

Gestion des sinistres et suivi des travaux

Déclaration fiscale et assistance administrative

Représentation en réunion de copropriété (optionnel)

Découvrez nos meilleures offres en gestion locative !

Contact & Informations

Adresse

📍 4 Rue Berzélius, 75017 Paris

Téléphone

📞 +33 1 42 63 63 63

Email

📩 assistance@francilienimmo.com

Accès à votre espace copropriétaire

📌 Identifiez-vous avec votre identifiant et mot de passe via notre portail en ligne.

Première connexion ? Munissez-vous de votre code inscrit sur votre appel de fonds ou courrier de bienvenue.

📞 N'hésitez pas à nous contacter pour plus d’informations ou une demande de rendez-vous !

"""
        ),
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=file_ids
    )
    return assistant

def check_thread_exists(wa_id):
    """
    Check if a thread exists for a given WhatsApp ID
    
    :param wa_id: WhatsApp ID
    :return: Thread ID if exists, None otherwise
    """
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id)

def store_thread(wa_id, thread_id):
    """
    Store a thread ID for a given WhatsApp ID
    
    :param wa_id: WhatsApp ID
    :param thread_id: Thread ID to store
    """
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

def run_assistant(thread, name):
    """
    Run the assistant for a given thread
    
    :param thread: Thread object
    :param name: User's name
    :return: Generated message
    """
    try:
        # Retrieve the Assistant
        assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

        # Wait for completion
        while run.status not in ["completed", "failed"]:
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == "failed":
            logging.error(f"Assistant run failed: {run.last_error}")
            return "Sorry, I'm experiencing some technical difficulties."

        # Retrieve the Messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        new_message = messages.data[0].content[0].text.value
        
        logging.info(f"Generated message for {name}")
        return new_message

    except Exception as e:
        logging.error(f"Error in running assistant: {e}")
        return "Sorry, I couldn't process your request at the moment."

def generate_response(message_body, wa_id, name):
    """
    Generate a response for a given message
    
    :param message_body: Incoming message
    :param wa_id: WhatsApp ID
    :param name: User's name
    :return: Generated response
    """
    # Check if thread exists
    thread_id = check_thread_exists(wa_id)

    # Create or retrieve thread
    if thread_id is None:
        logging.info(f"Creating new thread for {name}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
    else:
        logging.info(f"Retrieving existing thread for {name}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_body,
    )

    # Run assistant and get response
    return run_assistant(thread, name)