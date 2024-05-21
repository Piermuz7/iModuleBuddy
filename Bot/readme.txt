Creare cartella chiamata '.streamlit', dentro questa cartella creare file secrets.toml
In questo file andranno tutte le secret tipo api key di Anthropic e credenziali per il DB
Esempio:
ANTHROPIC_KEY = "chiavedianthropic"
NEO4J_URI = "urldeldb"

Comando da eseguire nel terminale in questa cartella per far partire il chatbot: streamlit run bot.py