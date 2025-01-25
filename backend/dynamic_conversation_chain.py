import os

from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from prompts import main_prompt_template

result = load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

memory = ConversationBufferMemory(memory_key="history", input_key="input")

dynamic_prompt = PromptTemplate.from_template(main_prompt_template)

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=api_key)

conversation_chain = LLMChain(llm=chat_model, prompt=dynamic_prompt, memory=memory)


def get_knowledge_from_database():
    data = """
{
    "event_title": "Konferencja Przyszłość AI 2025",
    "event_type": "Konferencja",
    "event_category": "Technologia",
    "event_subject": "Sztuczna Inteligencja",
    "event_date": "2025-03-15",
    "event_time": "09:00 - 17:00",
    "event_language": "Angielski",
    "event_fee": "Bezpłatne",
    "event_city": "San Francisco",
    "event_location": "Moscone Center",
    "event_location_address": "747 Howard St, San Francisco, CA 94103, USA",
    "event_registration_link": "https://www.futureofai2025.com/register",
    "event_webpage": "https://www.futureofai2025.com",
    "event_speakers": ["Dr. Jane Smith", "Prof. John Doe", "Elon Musk"],
    "event_agenda": "09:00 - Wystąpienie otwierające\n10:00 - Panel dyskusyjny: Etyka AI\n12:00 - Przerwa obiadowa\n13:00 - Warsztat: AI w opiece zdrowotnej\n15:00 - Sesja networkingowa\n16:00 - Zakończenie",
    "event_description": "Dołącz do nas na Konferencji Przyszłość AI 2025, gdzie liderzy branży i eksperci będą omawiać najnowsze osiągnięcia w dziedzinie sztucznej inteligencji. Wydarzenie obejmie szeroki zakres tematów, w tym etykę AI, zastosowania w opiece zdrowotnej oraz przyszłość technologii AI. Uczestnicy będą mieli okazję wziąć udział w warsztatach, panelach dyskusyjnych i sesjach networkingowych. Nie przegap tej okazji, aby uczyć się od najlepszych i nawiązać kontakty z profesjonalistami o podobnych zainteresowaniach.",
    "source": "https://unikonferencje.pl/#google_vignette"
},
{
    "event_title": "Szczyt Cyberbezpieczeństwa 2025",
    "event_type": "Szczyt",
    "event_category": "Technologia",
    "event_subject": "Cyberbezpieczeństwo",
    "event_date": "2025-05-20",
    "event_time": "10:00 - 18:00",
    "event_language": "Angielski",
    "event_fee": "$199",
    "event_city": "Nowy Jork",
    "event_location": "Javits Center",
    "event_location_address": "429 11th Ave, Nowy Jork, NY 10001, USA",
    "event_registration_link": "https://www.cybersummit2025.com/register",
    "event_webpage": "https://www.cybersummit2025.com",
    "event_speakers": ["Alice Johnson", "Robert Brown", "Sophia Lee"],
    "event_agenda": "10:00 - Wystąpienie otwierające\n11:00 - Wykład: Przyszłość cyberbezpieczeństwa\n13:00 - Przerwa obiadowa\n14:00 - Warsztat: Ochrona danych\n16:00 - Panel dyskusyjny: Zagrożenia cybernetyczne\n17:00 - Sesja networkingowa\n18:00 - Ceremonia zamknięcia",
    "event_description": "Szczyt Cyberbezpieczeństwa 2025 to wiodące wydarzenie dla profesjonalistów z dziedziny cyberbezpieczeństwa. Szczyt ten będzie obejmował wykłady czołowych ekspertów, interaktywne warsztaty oraz panele dyskusyjne na temat najnowszych trendów i zagrożeń w cyberbezpieczeństwie. Uczestnicy zdobędą cenne informacje na temat ochrony swoich organizacji przed cyberatakami oraz będą mieli okazję nawiązać kontakty z rówieśnikami i liderami branży. Zabezpiecz swoje miejsce już dziś i bądź na bieżąco z najnowszymi trendami w cyberbezpieczeństwie.",
    "source": "https://crossweb.pl/wydarzenia/it/"
},
{
    "event_title": "Expo Blockchain 2025",
    "event_type": "Expo",
    "event_category": "Technologia",
    "event_subject": "Blockchain",
    "event_date": "2025-07-10",
    "event_time": "08:00 - 16:00",
    "event_language": "Angielski",
    "event_fee": "$99",
    "event_city": "Londyn",
    "event_location": "ExCeL London",
    "event_location_address": "Royal Victoria Dock, 1 Western Gateway, Londyn E16 1XL, UK",
    "event_registration_link": "https://www.blockchainexpo2025.com/register",
    "event_webpage": "https://www.blockchainexpo2025.com",
    "event_speakers": ["Michael Green", "Laura White", "David Black"],
    "event_agenda": "08:00 - Rejestracja\n09:00 - Wystąpienie otwierające\n10:30 - Panel dyskusyjny: Blockchain w finansach\n12:00 - Przerwa obiadowa\n13:00 - Warsztat: Tworzenie rozwiązań blockchain\n15:00 - Sesja networkingowa\n16:00 - Zakończenie",
    "event_description": "Expo Blockchain 2025 to najważniejsze wydarzenie dla entuzjastów i profesjonalistów z dziedziny blockchain. Expo to zaprezentuje najnowsze innowacje w technologii blockchain oraz jej zastosowania w różnych branżach. Uczestnicy będą mieli okazję wysłuchać wystąpień czołowych prelegentów, wziąć udział w praktycznych warsztatach oraz zaangażować się w dyskusje na temat przyszłości blockchain. Niezależnie od tego, czy jesteś doświadczonym profesjonalistą, czy nowicjuszem w tej dziedzinie, Expo Blockchain 2025 oferuje coś dla każdego. Nie przegap tego ekscytującego wydarzenia!",
    "source": "https://www.eventbrite.com/d/poland/events/?_gl=1*11gow7e*_up*MQ..*_ga*NDUwNjUwMzMyLjE3Mzc3NDY4OTI.*_ga_TQVES5V6SH*MTczNzc0Njg5Mi4xLjAuMTczNzc0Njg5Mi4wLjAuMA.."
}
"""
    return data


def process_user_query(user_query):
    knowledge = get_knowledge_from_database()

    history = memory.load_memory_variables({}).get("history", "")

    inputs = {"knowledge": knowledge, "history": history, "input": user_query}

    prompt = dynamic_prompt.format(**inputs)

    response = conversation_chain.run(inputs)

    print("Generated prompt: ", prompt)
    print("AI: ", response)


while True:
    user_query = input("User: ")
    if user_query.lower() in ["quit", "exit"]:
        break

    process_user_query(user_query)
