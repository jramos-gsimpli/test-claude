from pathlib import Path

from dotenv import load_dotenv

from src import config
from src.agent import FileAgent
from src.chart_generator import ChartGenerator
from src.email_sender import EmailConfigError, EmailSender
from src.file_reader import FileReader, UnsupportedFileError

LOAD_PREFIX = "cargar "


def main() -> None:
    load_dotenv()
    agent = FileAgent(FileReader(), ChartGenerator())
    email_sender = EmailSender()

    exts = ", ".join(sorted(config.SUPPORTED_EXTENSIONS))
    print(f"Agente de análisis de archivos ({exts})")
    print("Comandos: 'cargar <ruta>' para cargar un archivo | 'salir' para terminar\n")

    while True:
        user_input = input("Vos: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            break

        if user_input.lower().startswith(LOAD_PREFIX):
            _handle_load(agent, email_sender, user_input[len(LOAD_PREFIX):].strip().strip("'\""))
        else:
            print(f"\nAgente: {agent.chat(user_input)}\n")


def _handle_load(agent: FileAgent, email_sender: EmailSender, path_str: str) -> None:
    path = Path(path_str)
    if not path.exists():
        print(f"\nAgente: No encontré el archivo '{path_str}'\n")
        return
    try:
        print("\nAgente: Analizando archivo...\n")
        summary = agent.load_file(path_str)
        print(f"Agente: {summary}\n")
        _send_summary_email(email_sender, path.name, summary)
    except UnsupportedFileError as e:
        print(f"\nAgente: {e}\n")


def _send_summary_email(email_sender: EmailSender, filename: str, summary: str) -> None:
    try:
        email_sender.send_summary(filename, summary)
        print("Agente: Resumen enviado por mail.\n")
    except EmailConfigError as e:
        print(f"Agente: Mail no enviado — {e}\n")
    except Exception as e:
        print(f"Agente: No se pudo enviar el mail: {e}\n")


if __name__ == "__main__":
    main()
