# Multi-AI-Agents V-Meeting Platform (v0.2)

[![YouTube Video Presentation](https://img.youtube.com/vi/GujQzX5TVqE/0.jpg)](https://www.youtube.com/watch?v=GujQzX5TVqE)

*[繁體中文版 README](README.zh-TW.md)*

Multi-AI-Agents V-Meeting Platform is an LLM-driven Multi AI Agents Group Meeting platform that allows multiple AI agents to engage in interactive discussions, simulating business meetings, creative brainstorming sessions, or academic debates. It features a pioneering web-based real-time visualization of the entire meeting process.

## Key Features

- **AI Agent Management**: Complete interface for creating, editing, and managing AI agents with custom personalities
- **AI Agent Interaction & Personalization**: Each AI character is powered by LLM with distinct personalities, expertise areas, and speaking styles
- **Meeting Process Management**: Support for custom topics, multi-round discussions, and role assignments
- **Visual Conversation Display**: Dynamic presentation of AI agent dialogues similar to real meeting scenarios
- **Meeting Records & Analysis**: Automatic generation of meeting minutes with key content summaries
- **Preset Character System**: Includes various functional "Pig Teammate" roles such as CEO, Marketing Manager, Sales Manager, etc.
- **Real-time Interaction**: Using WebSocket technology to ensure immediacy and coherence of conversation flow
- **Meeting Phase Control**: Includes introduction, discussion, and conclusion phases to simulate real meeting processes
- **Multi-round Discussion Support**: Configurable multi-round discussions with clear topics and objectives for each round
- **Meeting Record Export**: Support for exporting the entire meeting process in Markdown format for easy saving and sharing

## Technical Architecture

- **Frontend**: React + TailwindCSS
- **Backend**: Python (FastAPI)
- **AI Engine**: OpenAI API
- **Real-time Communication**: WebSocket
- **Data Storage**: Currently using in-memory storage, with plans to support databases in the future

## Quick Start

### Frontend Setup

```bash
# Enter the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

### Backend Setup

```bash
# Enter the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit the .env file and add your OpenAI API key

# Start the backend server
uvicorn app.main:app --reload
```

## System Architecture

```
/
├── frontend/                # React frontend
│   ├── public/              # Static files
│   └── src/
│       ├── components/      # UI components
│       ├── contexts/        # React Context
│       ├── pages/           # Page components
│       └── utils/           # Utility functions
├── backend/                 # Python backend
│   ├── app/                 # Main application
│   ├── models/              # Data models
│   └── utils/               # Utility functions
└── README.md                # Project description
```

## Usage Guide

1. After opening the application, you can configure the meeting topic, number of rounds, and participants in the setup panel
2. To manage AI agents, navigate to the "Agent Management" page where you can create, edit, or delete agents
3. After clicking the "Start Meeting" button, the system will automatically begin the meeting process
4. Each AI character will introduce themselves in turn, then enter the discussion phase
5. At the end of the meeting, the moderator will summarize the key points
6. You can export the meeting minutes at any time

## API Test Page

Access `http://localhost:8000/api-test` to open the API test page for:
- Checking OpenAI API connection status.
- Updating the API key temporarily for testing.
- Testing direct conversation with the LLM using the backend logic.

## Installation Guide

### System Requirements
- Node.js v14+
- Python 3.8+
- npm or yarn
- Valid OpenAI API Key (v1.x+ recommended for full compatibility with latest client library features)

### Complete Installation Steps

1. Clone the repository
   ```bash
   git clone https://github.com/mkhsu2002/Multi-AI-Agents-V-Meeting-Platform.git
   cd Multi-AI-Agents-V-Meeting-Platform
   ```

2. Install and start the backend
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   python run.py  # or use uvicorn app.main:app --reload
   ```

3. Install and start the frontend
   ```bash
   cd ../frontend
   npm install
   npm start
   ```

4. Access the application
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - API test page: http://localhost:8000/api-test

### Docker Installation (Local)

1. Install Docker and Docker Compose on your machine
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows and macOS
   - For Linux, follow [Docker Engine installation guide](https://docs.docker.com/engine/install/)

2. Clone the repository and navigate to the project directory
   ```bash
   git clone https://github.com/mkhsu2002/Multi-AI-Agents-V-Meeting-Platform.git
   cd Multi-AI-Agents-V-Meeting-Platform
   ```

3. Create .env file for the backend and add your OpenAI API key
   ```bash
   cp backend/.env.example backend/.env
   # Edit the .env file and add your OpenAI API key
   ```

4. Build and start the containers
   ```bash
   docker-compose up -d --build
   ```

5. Access the application
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - API test page: http://localhost:8000/api-test

6. Stop the containers when done
   ```bash
   docker-compose down
   ```

### Google Colab Setup

1. Open a new [Google Colab notebook](https://colab.research.google.com/)

2. Clone the repository and set up the backend
   ```python
   !git clone https://github.com/mkhsu2002/Multi-AI-Agents-V-Meeting-Platform.git
   %cd Multi-AI-Agents-V-Meeting-Platform/backend
   !pip install -r requirements.txt
   
   # Create .env file with your OpenAI API key
   %%writefile .env
   OPENAI_API_KEY=your_api_key_here
   ```

3. Install and configure ngrok to expose the backend server
   ```python
   !pip install pyngrok
   !ngrok authtoken YOUR_NGROK_AUTH_TOKEN  # Get from https://dashboard.ngrok.com/
   
   from pyngrok import ngrok
   # Start the backend server in the background
   !nohup python run.py &
   
   # Create a tunnel to the backend server
   public_url = ngrok.connect(8000)
   print(f"Backend is available at: {public_url}")
   ```

4. Update the frontend API configuration to use the ngrok URL
   ```python
   %cd ../frontend
   
   # Install Node.js packages in Colab (may take a few minutes)
   !npm install
   
   # Update API endpoint in the frontend to use ngrok URL
   # This is a simplified example - you may need to modify specific files
   !sed -i "s|http://localhost:8000|{public_url}|g" src/utils/api.js
   
   # Start the frontend (this will provide a link to access it)
   !npm start
   ```

5. Access the application through the link provided in the Colab output

## Customization and Extension

- You can add new UI elements or interactive features by modifying the frontend code
- The AI character generation logic and conversation flow can be adjusted through the backend code
- To add or edit AI agents, use the Agent Management interface at http://localhost:3000/agents
- You can also export your customized agents and share them with others

## Future Plans

- **Meeting Process Optimization**: Make the meeting process more logical and ensure effective meeting conclusions.
- **Multi-language Support**: Extend support to English, Japanese, and other languages in addition to Traditional Chinese
- **Multiple LLM API Support**: Extend support to Anthropic Claude, Google Gemini, local Ollama, and various other LLM APIs in addition to OpenAI
- **Different Meeting Scenario Templates**: Establish prompt templates for pig teammate AI agents based on different meeting scenarios such as collective creation, market analysis, creative inspiration, etc.
- **Database Integration**: Transition from in-memory storage to persistent storage, supporting meeting record queries
- **User Authentication System**: Add login functionality to support multi-user environments
- **Meeting Analysis Tools**: Provide more in-depth analysis of meeting content
- **Interface Aesthetics Optimization**: AI agent avatar generation, emotion recognition in dialogue windows
- **Community Sharing Features**: Meeting livestream functionality, meeting video downloads

## Acknowledgements

Thank you to [Microsoft TinyTroupe](https://github.com/microsoft/TinyTroupe/)! This project was conceptually inspired by Microsoft's TinyTroupe, but as the existing architecture did not fully meet the effects we wanted to achieve, we decided to rebuild from scratch. Our goal is to create a virtual meeting system where each AI agent is driven by LLM, and to provide a visual meeting presentation effect that allows users to intuitively experience the interaction and dialogue between AI agents.

## Contributions

We warmly welcome experts and developers from various fields to join this project! Whether you specialize in frontend development, backend architecture, UI design, prompt engineering, or LLM applications, you can contribute your talents here. If you have any ideas or suggestions, please feel free to submit a Pull Request or raise an Issue.

## Support Us

If you find this project helpful, you can support our development work by buying us a coffee!

<a href="https://buymeacoffee.com/mkhsu2002w" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

Your donation will be used for:
- Continued development and feature enhancement
- API fee payments
- System optimization and maintenance
- Community building and support

## License: MIT License

Additional terms: To respect the original contributors of this project, we require that all modified versions or derivative works based on this project clearly mark FlyPig AI in their documentation or code comments. For example:

* This project is modified based on FlyPig AI's TinyPigTroupe open-source project.
* This version is maintained by [Your Name/Company Name], based on contributions from FlyPig AI.

This requirement aims to ensure appropriate recognition of original contributions and promote good cooperation in the open-source community.