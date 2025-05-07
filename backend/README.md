# UAV Logger Chatbot Feature
This is an extension of the UAV Logger with a chatbot. The chatbot allows users to ask queries about uploaded MavLink data.

The UAV Logger Chatbot leverages an AI architecture to process and analyze telemetry data:

*   **Data Ingestion**: MavLink data is uploaded, parsed, and sent to the Python backend.
*   **Contextual Processing**: The chatbot, powered by LangGraph, determines which sections of data are relevant to the query.
*   **Intelligent Analysis**: Based on retrieved information, the system determines if mathematical reasoning or additional context is required.
*   **Memory Management**: Conversation history is maintained to provide context for follow-up questions.
*   **Frontend Integration**: A Vue.js component provides a UI for the chatbot.

## Chatbot Architecture

The chatbot uses a state-based flow with three primary components:

1. **Section Selector**: Analyzes the query to determine which data sections are needed
2. **Answer Generator**: Processes relevant data to produce an accurate response
3. **Memory Manager**: Maintains and updates conversation context

The system uses a combination of structured section selection and contextual memory to provide accurate and relevant responses.

### Data Processing

The chatbot can analyze various sections of telemetry data:

- Flight mode changes
- Events
- Mission waypoints
- Attitude data (roll, pitch, yaw)
- Trajectory information
- Text messages with severity levels
- Parameter changes
- Vehicle information

## Setup

### Create virtual environment

Create and activate the virtual environment via the following commands:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

# Installs
Install the required libraries for Python backend
```bash
pip install -r requirements.txt
```

Install the required node packages
```bash
npm install
```

### Env file setup
create an .env file with the following:
```bash
GEMINI_API_KEY="<your-api-key>"
```

### Run python backend server

```bash
cd ..  # Return to project root
uvicorn backend.main --reload --host 0.0.0.0 --port 8000
````

## Build setup
```bash
npm run dev
```

Open localhost:8080 to view app.

## Demo
https://github.com/user-attachments/assets/d6b01a57-26d4-43a8-ba59-3fed40a6042f

