import os
from pathlib import Path
from prompt_store import PromptStore
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = "mongodb+srv://lahiruprabhath099:qYVDTCA22Mds96KV@cluster1.diq5rte.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1&tlsAllowInvalidCertificates=true"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WORKSPACE_DIR = Path(os.path.join(os.getcwd(), "workspace"))
TEMPLATE_DIR = os.path.join(os.getcwd(), "templates/workspace")
PACKAGE_MANAGER = "npm"
MIN_NODE = (18, 18, 0)

store = PromptStore(MONGO_URI, db_name="GameOnAI", collection_name="prompts")

prompt_template = store.get_prompt("project_planner_prompt")    

INSTRUCTIONS= """ 
**Game Logic & Features:**
- AI opponents with multiple difficulty levels (Easy, Medium, Hard)
- Single-player vs AI 
- 2 players multiplayer option
- Single-Player vs AI feature should work without connecting to web Socket or not
- page.tsx should inside the app folder.
- Multiplayer game isn't not playing from the same device.
- Win/lose/draw condition detection with pixel-perfect accuracy
- Comprehensive error handling for all edge cases
- Player statistics and scoring system
- Eliminate lynting error and type defining errors

## UI/UX PRIORITY SPECIFICATIONS:

**Visual Design:**
- Modern, sleek interface with smooth micro-animations
- CRITICAL : Text colors, UI componenet allignments, spacing, utilizing the space as UX professionals.
- the playing areas should designed perfectly as match per the requested game.
- Space utilisation, deciding the size of each component, allignments, positioning should be world class
- No instructions and No dcumentaions.
- Eye catching Gradient backgrounds with dynamic color transitions
- Eye-catching color palettes with strategic color mixing
- Glassmorphism effects and card-based layouts
- Subtle shadows, borders, and depth effects
- Hover animations and interactive feedback
- Loading spinners, success states, and error notifications
- Minimal text, no guidelines or explanations
- Player turn indicators must be clear and immediate

##CRITICAL for MULTIPLAYER IMPLEMENTATION:

- Multiplayer game feature is only allowed to play via web soket implementaion in multiple devices. 
- But must not create join room UI feature in  multiplayer option. You can assume when game is opened it is created already.
- Understand that multiplayer game option is not playing in the same device. It is playing from two devices 
- UI States are update through the websocket in two players screen accordingly. 

CRITICAL : UI/UX components  positioning , color mixing ,player turns return should be world class
Use filled color game objects. Less Text , no guidelines or explanations in the UI
"""

summarizer_prompt = """You are a game development requirements analyzer. Your task is to extract and summarize the core game concept and requirements from user queries, focusing only on gameplay mechanics, features, and user experience elements.

INSTRUCTIONS:
1. Extract the main game concept and identify the specific game type
2. Summarize ONLY the gameplay requirements, features, and mechanics
3. Ignore all technical implementation details including:
   - Database implementations
   - WebSocket connections
   - API specifications
   - Server architecture
   - Programming languages
   - Framework choices
   - Deployment details
   - Technical stack mentions

4. Focus on:
   - Game mechanics and rules
   - Player interactions
   - Game objectives and win conditions
   - UI/UX requirements
   - Visual elements and themes
   - Game modes or difficulty levels
   - Player progression systems
   - Core features and functionality

5. Return your response in this exact JSON format:
{{
    "summarized_text": "Clear, concise summary of the game requirements focusing on gameplay mechanics, features, and user experience",
    "game_name": "Identified game type or name (e.g., 'tic_tac_toe', 'snake_game', 'puzzle_game', 'platformer', etc.)"
}}

EXAMPLES:

Input: "I want to build a tic-tac-toe game with React and Node.js backend, using WebSocket for real-time multiplayer and MongoDB for storing game states"
Output: {{
    "summarized_text": "A classic tic-tac-toe game where two players take turns placing X's and O's on a 3x3 grid, with the goal of getting three marks in a row (horizontally, vertically, or diagonally). Features real-time multiplayer gameplay.",
    "game_name": "tic_tac_toe"
}}

Input: "Create a snake game using Python with pygame, store high scores in SQLite database and implement collision detection algorithms"
Output: {{
    "summarized_text": "A snake game where the player controls a growing snake to eat food while avoiding collisions with walls and the snake's own body. Features score tracking and high score system.",
    "game_name": "snake_game"
}}

Now analyze the following user query and return the JSON response:

{user_query}"""


sample_prompt = """You are an expert Next.js developer. continue a incomplete game development project following the guidelines.

**user_query:** {requirements}

Return a JSON object with this exact structure. No string literal output. The files field should be a list not a string literal. Also the object inside the file list should not be string json text. It should be a JSON type object:

```json
{{
    "description": "Brief project description",
    "development_plan": "Development plan overview",
    "directories": ["app/components", "app/hooks", "app/types"],
    "files": [
        {{
            "path": "app/file1.tsx",
            "description": "File description", 
            "content": "complete functional code"
        }}
    ],
    "packages": [
        {{
            "name": "package-name",
            "dev": false
        }}
    ]
}}
```

***Guidelines***
***CRITICAL*** 
Your goal is to continue from the avialble web socket connection.


**Game Logic & Features:**
- continue game implementaion. creat  components like, types and page.tsx,
- db connection already implemented. 
- AI opponents with multiple difficulty levels (Easy, Medium, Hard)
- Single-Player vs AI and - Multi player options
- multiplayer option feature should work without connecting to web Socket
- Create seperate componenets, type defenitions 
- componenets folder, types folder, hooks folder, page.tsx must be inside the app folder.
- Multiplayer game isn't not playing from the same device. It is playing from two devices
- Win/lose/draw condition detection with pixel-perfect accuracy
- Comprehensive error handling for all edge cases
- Player statistics and scoring system
- Eliminate lynting error and type defining errors

## UI/UX PRIORITY SPECIFICATIONS:

**Visual Design:**
- Modern, sleek interface with smooth micro-animations
- CRITICAL : Text colors, UI componenet allignments, spacing, utilizing the space as UX professionals.
- the playing areas should designed perfectly as match per the requested game.
- Space utilisation, deciding the size of each component, allignments, positioning should be world class
- No instructions and No dcumentaions.
- Eye catching Gradient backgrounds with dynamic color transitions
- Eye-catching color palettes with strategic color mixing
- Glassmorphism effects and card-based layouts
- Subtle shadows, borders, and depth effects
- Hover animations and interactive feedback
- Loading spinners, success states, and error notifications
- Minimal text, no guidelines or explanations
- Player turn indicators must be clear and immediate 


##Important for MULTIPLAYER IMPLEMENTATION:
I'll provide an example codes how the multiplayer game is implemented. you want to use exact websocket and api related concept variables names as exactly as same.
see the example code  below to handle states in each player device  with multiplayer support. The example is to guioide to the multiplayer connection setup. the game play and componenet should design according the required game

{main_page}



## **CRITICAL FOR MULTIPLAYER OPTION - **
- Multiplayer games ONLY via WebSocket on multiple devices (not same device)
- NO join room UI - assume game room already created when opened
- Use EXACTLY the same payload variables, state variables, API names, event names as reference example
- Handle all socket events in page.tsx according to requested game
- gameSessionUUID value must be parsed from params in page.tsx
- Define all type definitions in page.tsx
- Do NOT create additional APIs
- Player names should display by actual name and profile accordingly

## PLAYER TURN DISPLAY
- When player turns change, display logically updates on each user's screen
- UI states update through WebSocket across both players' screens simultaneously


## IMPLEMENTATION
- Extract gameSessionUUID by parsing URL parameters in page.tsx
- Create game components in component folder
- Game logic and UI adapt to requested game while maintaining WebSocket structure
- Real-time state synchronization between separate devices
"""



fixer_prompt = """You are a Next.js/TypeScript code fixer. You MUST generate fix actions.

BUILD ERROR: {error}
ROOT CAUSE: {root_cause}
CURRENT CODE: {current_code}

CRITICAL RULE: Since an error exists, you MUST provide at least one action. Empty actions = system failure.

MANDATORY OUTPUT STRUCTURE:
{{
  "summary": "Error type and fix method",
  "actions": [REQUIRED - CANNOT BE EMPTY]
}}

FORCE ACTION GENERATION:
If you identify the fix but hesitate to provide actions, you MUST still provide them.
If you're unsure of exact content, provide your best attempt rather than empty actions.
If you can't determine the exact file, use the most likely file path from the error.

COMMON ERROR → ACTION MAPPING:
- Type error → write_file with type fix
- Import error → write_file with correct imports  
- Missing package → install_package
- Syntax error → write_file with syntax fix
- Any other error → write_file with attempted fix- 
- Hardly skip warnings. No need to fix
- You have two task mainly
    1 - fix the error.
    2 - Must provide the rewrite content with fix in actions key

EMERGENCY FALLBACK (if no specific fix identified):
Always include at least this action:
{{"tool": "write_file", "args": {{"path": "[most_likely_file_from_error]", "content": "[current_code_with_obvious_fix_attempt]"}}

VALIDATION CHECK:
- Before responding, verify actions array is NOT empty
- If actions is empty, add a fallback write_file action
- Never explain why you can't fix - just provide your best fix attempt

RESPONSE (JSON only):
{{
  "summary": "Brief fix description", 
  "actions": [{{"tool": "write_file", "args": {{"path": "file.ts", "content": "complete fixed file content"}}]
}}"""


improver_prompt = """
You are an expert Next.js developer with 10+ years of experience building production-grade applications. You specialize in game development and have a track record of maintaining high-quality, stable codebases.

## CONTEXT
- Initial Project: {instructions}
- Change Request: {requirement}
- Target Code: {codes}

## YOUR MISSION
Analyze the provided code and implement the requested changes with surgical precision. This is a WORKING system that requires minimal, targeted modifications.

## CRITICAL CONSTRAINTS
1. **Preserve Functionality**: The current code is stable and functional - make only necessary changes
2. **Minimal Impact**: Avoid refactoring or "improvements" beyond the specific requirement
3. **Precision Over Perfection**: Focus on the exact change requested, not code optimization
4. **Risk Assessment**: If the change could break existing functionality, explain the risks

## ANALYSIS PROCESS
1. **Understand**: What specific functionality needs to change?
2. **Locate**: Which exact files/sections require modification?
3. **Isolate**: What's the minimal change that satisfies the requirement?
4. **Implement**: Apply changes while preserving existing code patterns
5. **Do not** change any route.ts file if provided in any case. They are provided to as helpers to change other required files

## RESPONSE FORMAT
The √ name should return as it is provided in the Target code section.
You MUST respond with a valid JSON object in this exact format:

{{
  "changes": [
    {{
      "file_path": "file_path_1",
      "content": "complete_rewritten_file_content_with_changes_applied"
    }},
    {{
      "file_path": "file_path", 
      "content": "complete_rewritten_file_content_with_changes_applied"
    }}
  ],
  "description": "Brief explanation of changes made or additional information needed"
}}

## SPECIAL CASES
If the change requested cannot be achieved by modifying the target code (it might require additional files, dependencies, or information not provided), respond with an empty changes list and use the description field to request the additional information needed to complete the task.

Example for cases requiring additional information:
{{
  "changes": [],
  "description": "Cannot complete the requested change. Additional information needed: [specify what's missing - e.g., missing component files, required dependencies, configuration files, etc.]"
}}
"""