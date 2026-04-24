import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .chart_generator import ChartGenerator, ChartGenerationError
from .file_reader import FileContent, FileReader

SYSTEM_PROMPT = """Sos un analista de datos experto. El usuario te carga archivos PDF, CSV o Excel
y vos los analizás, respondés preguntas y generás gráficos.

Lineamientos:
- Resumís el contenido de forma clara y concisa al cargar un archivo
- Respondés preguntas con valores exactos del archivo
- Para gráficos usás la herramienta generar_grafico (solo disponible con CSV/Excel)
- Si el usuario pide algo imposible con los datos disponibles, lo explicás brevemente
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generar_grafico",
            "description": "Genera y guarda un gráfico a partir de los datos del archivo CSV/Excel cargado",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["barras", "linea", "torta", "dispersion", "histograma"],
                    },
                    "columna_x": {
                        "type": "string",
                        "description": "Columna para eje X o categorías (torta)",
                    },
                    "columna_y": {
                        "type": "string",
                        "description": "Columna para eje Y (no requerida en histograma)",
                    },
                    "titulo": {"type": "string"},
                    "top_n": {
                        "type": "integer",
                        "description": "Limitar a los N registros más altos por columna_y",
                    },
                },
                "required": ["tipo", "columna_x", "titulo"],
            },
        },
    }
]


class FileAgent:
    def __init__(self, reader: FileReader, chart_gen: ChartGenerator):
        self._reader = reader
        self._chart_gen = chart_gen
        self._client = OpenAI()
        self._messages: List[Dict[str, Any]] = []
        self._loaded_file: Optional[FileContent] = None

    def load_file(self, path: str) -> str:
        self._loaded_file = self._reader.read(path)
        self._messages = []
        return self.chat(
            f"Acabo de cargar este archivo. Hacé un resumen conciso:\n\n{self._loaded_file.context_text}"
        )

    def chat(self, user_input: str) -> str:
        self._messages.append({"role": "user", "content": user_input})

        while True:
            has_tabular_data = self._loaded_file and self._loaded_file.dataframe is not None
            response = self._client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2048,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self._messages,
                tools=TOOLS if has_tabular_data else [],
            )

            message = response.choices[0].message
            self._messages.append(message)

            if response.choices[0].finish_reason == "stop" or not message.tool_calls:
                return message.content or ""

            tool_results = [
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": self._run_tool(tc.function.name, json.loads(tc.function.arguments)),
                }
                for tc in message.tool_calls
            ]
            self._messages.extend(tool_results)

    def _run_tool(self, name: str, inputs: Dict[str, Any]) -> str:
        if name != "generar_grafico" or not self._loaded_file or self._loaded_file.dataframe is None:
            return "Error: no hay datos tabulares cargados."

        try:
            path = self._chart_gen.generate(
                df=self._loaded_file.dataframe,
                tipo=inputs["tipo"],
                columna_x=inputs["columna_x"],
                titulo=inputs["titulo"],
                columna_y=inputs.get("columna_y"),
                top_n=inputs.get("top_n"),
            )
            return f"Gráfico guardado en: {path}"
        except ChartGenerationError as e:
            return f"Error al generar el gráfico: {e}"
