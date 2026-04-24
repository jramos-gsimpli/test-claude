import json
from unittest.mock import MagicMock, patch

import pytest

from src.agent import FileAgent
from src.chart_generator import ChartGenerator
from src.file_reader import FileReader


def _response(finish_reason: str, content: str = "", tool_calls=None) -> MagicMock:
    choice = MagicMock()
    choice.finish_reason = finish_reason
    choice.message.content = content
    choice.message.tool_calls = tool_calls
    response = MagicMock()
    response.choices = [choice]
    return response


def _tool_call(tool_id: str, name: str, arguments: dict) -> MagicMock:
    tc = MagicMock()
    tc.id = tool_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


@pytest.fixture
def agent():
    with patch("src.agent.OpenAI"):
        ag = FileAgent(MagicMock(spec=FileReader), MagicMock(spec=ChartGenerator))
        ag._client = MagicMock()
        return ag


def test_chat_returns_final_text(agent):
    agent._client.chat.completions.create.return_value = _response("stop", "Hola.")
    assert agent.chat("hola") == "Hola."


def test_load_file_resets_messages(agent, csv_file_content):
    agent._reader.read.return_value = csv_file_content
    agent._messages = [{"role": "user", "content": "anterior"}]
    agent._client.chat.completions.create.return_value = _response("stop", "Resumen.")
    agent.load_file("data.csv")
    assert len(agent._messages) == 2


def test_tool_call_generates_chart(agent, csv_file_content):
    agent._loaded_file = csv_file_content
    agent._chart_gen.generate.return_value = "graficos/Test.png"
    agent._client.chat.completions.create.side_effect = [
        _response("tool_calls", tool_calls=[_tool_call("t1", "generar_grafico", {"tipo": "barras", "columna_x": "producto", "columna_y": "ventas", "titulo": "Test"})]),
        _response("stop", "Gráfico generado."),
    ]
    result = agent.chat("hacé un gráfico de barras")
    agent._chart_gen.generate.assert_called_once()
    assert result == "Gráfico generado."


def test_no_tools_for_pdf(agent, pdf_file_content):
    agent._loaded_file = pdf_file_content
    agent._client.chat.completions.create.return_value = _response("stop", "Ok.")
    agent.chat("resumí")
    call_kwargs = agent._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["tools"] == []
