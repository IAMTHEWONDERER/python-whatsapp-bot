from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


# --------------------------------------------------------------
# Upload file
# --------------------------------------------------------------
def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file


file = upload_file("../data/data.pdf")


# --------------------------------------------------------------
# Create assistant
# --------------------------------------------------------------
def create_assistant(file):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="Hamza",
        instructions=(
            "Communicate in French, English, or Arabic based on user's language. talk about this service in a we terms, as in ur their agent"
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
        file_ids=[file.id],
    )
    return assistant


assistant = create_assistant(file)


# --------------------------------------------------------------
# Thread management
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


# --------------------------------------------------------------
# Generate response
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    return new_message


# --------------------------------------------------------------
# Run assistant
# --------------------------------------------------------------
def run_assistant(thread):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve("asst_EWr7vif4A0pFhSRoilKLw899")

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    print(f"Generated message: {new_message}")
    return new_message


# --------------------------------------------------------------
# Test assistant
# --------------------------------------------------------------

new_message = generate_response("What's the check in time?", "123", "John")

new_message = generate_response("What's the pin for the lockbox?", "456", "Sarah")

new_message = generate_response("What was my previous question?", "123", "John")

new_message = generate_response("What was my previous question?", "456", "Sarah")
