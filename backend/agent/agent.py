import json
import re
from typing import List, Literal, Dict, Any, TypedDict, Union
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from backend.services.settings_service import SettingsService
from langgraph.graph import StateGraph, END

# Pydantic schema for structured section choice
template_sections = [
    "flightModeChanges", "events", "mission", "attitude",
    "trajectories", "textMessages", "params", "vehicle"
]

class SectionChoice(BaseModel):
    sections: List[Literal[
        "flightModeChanges", "events", "mission", "attitude",
        "trajectories", "textMessages", "params", "vehicle"
    ]] = Field(..., description="Chosen telemetry sections")

# Agent state definition
typing_HM = Union[HumanMessage, AIMessage, SystemMessage]
class AgentState(TypedDict):
    messages: List[typing_HM]
    parsed_data: Dict[str, Any]
    selected_sections: List[str]

class Agent:
    def __init__(self, parsed_data: Dict[str, Any], llm=None):
        self.llm = llm or ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=SettingsService().settings.gemini_api_key
        )
        self.parsed_data = parsed_data
        self.available_sections = template_sections
        self.section_parser = PydanticOutputParser(pydantic_object=SectionChoice)
        self.section_descriptions = (
            "flightModeChanges: list of [time (in milliseconds), flightMode]\n"
            "events: list of [time (in milliseconds), event]\n"
            "mission: list of [latitude, longitude, altitude]\n"
            "attitude: dictionary mapping { time (in milliseconds): [roll, pitch, yaw]}\n"
            "trajectories: list of [longitude, latitude, relative altitude, time (in milliseconds)]\n"
            "textMessages: list of [time (in milliseconds), severity, text_message] severity is measured as the following:\n"
            "0=emergency, 1=alert, 2=critical, 3=error, 4=warning, 5=notice, 6=info, 7=debug"
            "params: dictionary mapping { values: {param: initial_value}, changeArray: [[time (in milliseconds), param, value]] }\n"
            "vehicle: string describing vehicle type (e.g., 'quadcopter')"
        )
        selector_template = PromptTemplate(
            input_variables=["sections", "question", "format_instructions", "section_descriptions"],
            template="""
            You have access to these telemetry sections:
            {sections}

            Descriptions:
            {section_descriptions}

            User question: "{question}"

            {format_instructions}

            Reply ONLY with the JSON format specifying your chosen sections (or empty list if none). Be generous.
            """
        )
        self.structured_selector = selector_template | self.llm
        answer_template = PromptTemplate(
            input_variables=["selected_sections", "data", "question"],
            template="""
            Here are the extracted sections:
            {data}

            User question: "{question}"

            If the question involves time calculations (duration, intervals, etc.):
            1. Identify all relevant timestamps across provided sections
            2. Determine the appropriate calculation method (min/max for duration, sequence analysis for patterns)
            3. Include units in your answer (milliseconds, seconds, minutes)

            Based on the conversation and this data, provide a direct, clear, accurate answer. Don't make the reasoning section too long. Ask for clarifications if needed.
            """
        )
        self.answer_chain = answer_template | self.llm
        self._setup_graph()
        system_msg = SystemMessage(content="""You are an expert UAV telemetry analyst chatbot assistant.\nYou help users understand UAV flight data.\n""")
        self.state: AgentState = {
            "messages": [system_msg],
            "parsed_data": self.parsed_data,
            "selected_sections": []
        }

    def _setup_graph(self):
        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("select_sections", self._select_sections)
        self.workflow.add_node("generate_answer", self._generate_answer)
        self.workflow.add_edge("select_sections", "generate_answer")
        self.workflow.add_edge("generate_answer", END)
        self.workflow.set_entry_point("select_sections")
        self.graph = self.workflow.compile()

    def _select_sections(self, state: AgentState) -> AgentState:
        question = state["messages"][-1].content
        format_instructions = self.section_parser.get_format_instructions()
        selector_input = {
            "sections": ", ".join(self.available_sections),
            "question": question,
            "format_instructions": format_instructions,
            "section_descriptions": self.section_descriptions
        }
        output = self.structured_selector.invoke(selector_input)
        raw = output.content if hasattr(output, 'content') else str(output)
        matches = re.findall(r'({[\s\S]*?})', raw)
        selected = []
        for js in matches:
            try:
                obj = json.loads(js)
                if isinstance(obj, dict) and "sections" in obj:
                    selected = [s for s in obj["sections"] if s in self.available_sections]
                    break
            except json.JSONDecodeError:
                continue
        if not selected:
            try:
                parsed = self.section_parser.parse(raw)
                selected = [s for s in parsed.sections if s in self.available_sections]
            except Exception:
                selected = self.available_sections
        state["selected_sections"] = selected
        return state

    def _generate_answer(self, state: AgentState) -> AgentState:
        question = state["messages"][-1].content
        secs = state.get("selected_sections", self.available_sections)
        data_slice = {k: state["parsed_data"].get(k) for k in secs}
        answer_input = {
            "selected_sections": secs,
            "data": json.dumps(data_slice, indent=2),
            "question": question
        }
        ans_out = self.answer_chain.invoke(answer_input)
        text = ans_out.content if hasattr(ans_out, 'content') else str(ans_out)
        state["messages"].append(AIMessage(content=text))
        return state

    def chat(self, user_input: str) -> str:
        self.state["messages"].append(HumanMessage(content=user_input))
        self.state = self.graph.invoke(self.state)
        for msg in reversed(self.state["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        return ""

def start_chatbot(json_file_path: str):
    with open(json_file_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)
    agent = Agent(parsed_data)
    print("UAV Telemetry Assistant ('exit' to quit)")
    print("-" * 50)
    while True:
        try:
            user_input = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if user_input.strip().lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        response = agent.chat(user_input)
        print(f"\nAssistant: {response}")

if __name__ == "__main__":
    path = "backend/telemetry_dump_sample.json"
    start_chatbot(path)