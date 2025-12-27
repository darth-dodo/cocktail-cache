# Cocktail Cache - Architecture Diagrams

> Visual representations of system architecture, data flow, and component interactions using Mermaid diagrams.

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Client["Browser (HTMX)"]
        UI[Web Interface]
        LS[(Local Storage)]
    end

    subgraph Server["FastAPI Server"]
        API[API Routes]
        Flow[Cocktail Flow]
        Session[(Session Cache)]
    end

    subgraph CrewAI["CrewAI Engine"]
        Crew1[Analysis Crew]
        Crew2[Recipe Crew]
    end

    subgraph Data["Static Data"]
        Cocktails[(cocktails.json)]
        Mocktails[(mocktails.json)]
        Unlock[(unlock_scores.json)]
    end

    subgraph External["External Services"]
        Claude[Anthropic Claude API]
    end

    UI <-->|HTTP/HTMX| API
    LS <-->|Read/Write| UI
    API --> Flow
    Flow --> Crew1
    Flow --> Crew2
    Crew1 --> Claude
    Crew2 --> Claude
    Crew1 --> Data
    Crew2 --> Data
    Flow --> Session
```

---

## 2. Request/Response Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant LS as Local Storage
    participant API as FastAPI
    participant F as Flow
    participant C1 as Analysis Crew
    participant C2 as Recipe Crew
    participant LLM as Claude API

    B->>LS: Load cabinet, prefs, history
    LS-->>B: Stored data

    B->>API: POST /api/recommend
    Note over B,API: {cabinet, mood, drink_type,<br/>skill_level, recent_history}

    API->>F: Create CocktailFlowState

    F->>C1: Analyze cabinet + mood
    C1->>LLM: Cabinet Analyst (1 call)
    LLM-->>C1: Candidates
    C1->>LLM: Mood Matcher (1 call)
    LLM-->>C1: Ranked list
    C1-->>F: Top candidates

    F->>C2: Generate recipe
    C2->>LLM: Recipe Writer (1 call)
    LLM-->>C2: Full recipe
    C2->>LLM: Bottle Advisor (1 call)
    LLM-->>C2: Next bottle
    C2-->>F: Recipe + recommendation

    F-->>API: Complete response
    API-->>B: JSON response

    B->>B: Render recipe card

    Note over B,LLM: Total: ~4 LLM calls, <8 seconds
```

---

## 3. CrewAI Agent Architecture

```mermaid
flowchart TB
    subgraph Input["User Input"]
        cabinet[Cabinet]
        mood[Mood]
        dtype[Drink Type]
        skill[Skill Level]
        history[Recent History]
    end

    subgraph Crew1["CREW 1: Analysis"]
        direction TB
        CA[Cabinet Analyst]
        MM[Mood Matcher]
        CA -->|candidates| MM
    end

    subgraph Crew2["CREW 2: Recipe"]
        direction TB
        RW[Recipe Writer]
        BA[Bottle Advisor]
        RW --> BA
    end

    subgraph Tools["Tools (Deterministic)"]
        RDB[(RecipeDB)]
        FP[(FlavorProfiler)]
        SF[(SubstitutionFinder)]
        UC[(UnlockCalculator)]
    end

    subgraph Output["Response"]
        recipe[Recipe + Tips]
        bottle[Next Bottle]
        why[Why This Drink]
    end

    Input --> CA
    CA --> RDB
    MM --> FP
    Crew1 -->|selected cocktail| RW
    RW --> RDB
    RW --> SF
    BA --> UC
    Crew2 --> Output
```

---

## 4. Agent Details

```mermaid
flowchart LR
    subgraph CA["Cabinet Analyst"]
        CA_in["Input:<br/>• cabinet[]<br/>• drink_type<br/>• skill_level<br/>• exclude[]"]
        CA_out["Output:<br/>• candidates[]<br/>• match_scores<br/>• difficulty<br/>• is_mocktail"]
        CA_tool["Tool: RecipeDB"]
    end

    subgraph MM["Mood Matcher"]
        MM_in["Input:<br/>• mood<br/>• constraints[]<br/>• candidates[]<br/>• skill_level"]
        MM_out["Output:<br/>• ranked[]<br/>• why (explanation)<br/>• flavor_profiles"]
        MM_tool["Tool: FlavorProfiler"]
    end

    subgraph RW["Recipe Writer"]
        RW_in["Input:<br/>• cocktail_id<br/>• user_cabinet<br/>• skill_level"]
        RW_out["Output:<br/>• full recipe<br/>• skill-adapted tips<br/>• substitutions"]
        RW_tool["Tools: RecipeDB,<br/>SubstitutionFinder"]
    end

    subgraph BA["Bottle Advisor"]
        BA_in["Input:<br/>• cabinet[]<br/>• preferred_profiles"]
        BA_out["Output:<br/>• best bottle<br/>• unlocks[]<br/>• price range<br/>• runner-up"]
        BA_tool["Tool: UnlockCalculator"]
    end
```

---

## 5. Data Architecture

```mermaid
flowchart TB
    subgraph ServerData["Server-Side Data (JSON Files)"]
        direction LR
        cocktails["cocktails.json<br/>50 recipes"]
        mocktails["mocktails.json<br/>20+ recipes"]
        ingredients["ingredients.json<br/>Categorized"]
        subs["substitutions.json<br/>Swap mappings"]
    end

    subgraph BuildTime["Build Time Processing"]
        script["compute_unlock_scores.py"]
    end

    subgraph Computed["Pre-Computed Data"]
        unlock["unlock_scores.json<br/>Bottle → Unlocked drinks"]
    end

    subgraph ClientData["Client-Side Storage (localStorage)"]
        direction LR
        cabinet["cocktail-cache-cabinet<br/>[bourbon, gin, ...]"]
        prefs["cocktail-cache-prefs<br/>{skill_level, drink_type}"]
        history["cocktail-cache-history<br/>[{recipe_id, made_at}]"]
    end

    cocktails --> script
    mocktails --> script
    script --> unlock

    ServerData --> Tools
    Computed --> Tools

    subgraph Tools["CrewAI Tools"]
        RecipeDB
        FlavorProfiler
        SubstitutionFinder
        UnlockCalculator
    end
```

---

## 6. Data Models

```mermaid
classDiagram
    class Recipe {
        +str id
        +str name
        +str tagline
        +str why
        +FlavorProfile flavor_profile
        +list~RecipeIngredient~ ingredients
        +list~PrepStep~ prep
        +list~RecipeStep~ method
        +str glassware
        +str garnish
        +str timing
        +str difficulty
        +list~TechniqueTip~ technique_tips
        +list~Variation~ variations
        +bool is_mocktail
    }

    class FlavorProfile {
        +int sweet
        +int sour
        +int bitter
        +int spirit
    }

    class CocktailMatch {
        +str cocktail_id
        +str name
        +float match_score
        +list~str~ missing
        +bool substitutable
        +str difficulty
        +bool is_mocktail
    }

    class UserPreferences {
        +str skill_level
        +str drink_type
        +int exclude_count
    }

    class HistoryEntry {
        +str recipe_id
        +str recipe_name
        +datetime made_at
        +bool is_mocktail
    }

    class CocktailFlowState {
        +str session_id
        +list~str~ cabinet
        +str mood
        +list~str~ constraints
        +str drink_type
        +str skill_level
        +list~str~ recent_history
        +list~CocktailMatch~ candidates
        +str selected
        +Recipe recipe
        +BottleRecommendation next_bottle
        +list~str~ rejected
    }

    Recipe --> FlavorProfile
    CocktailFlowState --> CocktailMatch
    CocktailFlowState --> Recipe
```

---

## 7. UI Component Architecture

```mermaid
flowchart TB
    subgraph Page["index.html"]
        subgraph InputSection["Input Section"]
            DrinkToggle["drink_type_toggle.html<br/>Cocktail | Mocktail | Both"]
            SkillSelect["skill_selector.html<br/>Beginner | Intermediate | Adventurous"]
            CabinetGrid["cabinet_grid.html<br/>Collapsible ingredient categories"]
            MoodSelect["mood_selector.html<br/>Unwinding | Celebrating | Impressing | Quick"]
            Submit["Make Me Something Button"]
        end

        subgraph ResultSection["#result (HTMX Target)"]
            RecipeCard["recipe_card.html"]
            FlavorChart["flavor_chart.html"]
            NextBottle["next_bottle.html"]
        end

        subgraph HistorySection["History Section"]
            HistoryList["history_list.html<br/>Recently Made drinks"]
        end
    end

    DrinkToggle --> Submit
    SkillSelect --> Submit
    CabinetGrid --> Submit
    MoodSelect --> Submit
    Submit -->|"hx-post=/api/recommend<br/>hx-target=#result"| ResultSection
    RecipeCard --> FlavorChart
```

---

## 8. Recipe Card Component

```mermaid
flowchart TB
    subgraph RecipeCard["recipe_card.html"]
        Header["Header: Name + Badges<br/>[EASY] [🍸 COCKTAIL]"]
        Tagline["Tagline"]
        Why["Why This Drink section"]

        subgraph TwoCol["Two Column Layout"]
            Flavor["Flavor Profile Chart<br/>Sweet/Sour/Bitter/Spirit bars"]
            Ingredients["Ingredients List<br/>with amounts"]
        end

        Method["Step-by-step Method<br/>with technique tips"]

        subgraph Actions["Action Buttons"]
            Another["Show Me Another"]
            Made["I Made This ✓"]
        end

        NextBottle["Next Bottle Recommendation<br/>with unlock list"]
    end

    Header --> Tagline --> Why --> TwoCol --> Method --> Actions --> NextBottle
```

---

## 9. State Machine - User Session

```mermaid
stateDiagram-v2
    [*] --> FirstVisit: User opens app

    FirstVisit --> InputReady: Load from localStorage<br/>(or defaults)

    InputReady --> Processing: Click "Make Me Something"

    Processing --> RecipeView: CrewAI Flow completes<br/>(~4-8 seconds)

    RecipeView --> Processing: "Show Me Another"<br/>(adds to rejected[])

    RecipeView --> HistoryUpdate: "I Made This"

    HistoryUpdate --> InputReady: Save to localStorage

    RecipeView --> InputReady: Start Over

    note right of Processing
        4 LLM calls
        Target: <8 sec
    end note

    note right of HistoryUpdate
        Updates localStorage:
        - cocktail-cache-history
    end note
```

---

## 10. Flow State Transitions

```mermaid
stateDiagram-v2
    direction LR

    [*] --> ReceiveInput

    ReceiveInput --> Analyze: State initialized
    note right of ReceiveInput
        Sets:
        • session_id
        • cabinet
        • mood
        • drink_type
        • skill_level
        • recent_history
    end note

    Analyze --> GenerateRecipe: Crew 1 complete
    note right of Analyze
        Sets:
        • candidates[]
        • selected
    end note

    GenerateRecipe --> Complete: Crew 2 complete
    note right of GenerateRecipe
        Sets:
        • recipe
        • next_bottle
    end note

    Complete --> [*]
```

---

## 11. Deployment Architecture

```mermaid
flowchart TB
    subgraph Internet
        Users[Users]
    end

    subgraph FlyEdge["Fly.io Edge (Global CDN)"]
        CDN[CDN / Load Balancer]
    end

    subgraph FlyRegion["Fly.io Region"]
        subgraph Container["Docker Container"]
            Uvicorn[Uvicorn ASGI]
            FastAPI[FastAPI App]
            CrewAI[CrewAI Engine]

            subgraph StaticData["Static Data Volume"]
                JSON[(JSON Files)]
            end
        end
    end

    subgraph Anthropic["Anthropic"]
        Claude[Claude API]
    end

    Users --> CDN
    CDN --> Uvicorn
    Uvicorn --> FastAPI
    FastAPI --> CrewAI
    CrewAI --> JSON
    CrewAI --> Claude
```

---

## 12. Performance Budget

```mermaid
gantt
    title Request Timeline Target (<8 seconds)
    dateFormat X
    axisFormat %s

    section Request
    Parse Input           :0, 200

    section Crew 1
    Cabinet Analyst (LLM) :200, 1700
    Mood Matcher (LLM)    :1700, 3200

    section Crew 2
    Recipe Writer (LLM)   :3200, 5200
    Bottle Advisor (LLM)  :5200, 7200

    section Response
    Build Response        :7200, 7500
    Network Transfer      :7500, 8000
```

---

## 13. Tool Dependencies

```mermaid
flowchart LR
    subgraph Agents
        CA[Cabinet Analyst]
        MM[Mood Matcher]
        RW[Recipe Writer]
        BA[Bottle Advisor]
    end

    subgraph Tools
        RDB[RecipeDB]
        FP[FlavorProfiler]
        SF[SubstitutionFinder]
        UC[UnlockCalculator]
    end

    subgraph Data
        C[(cocktails.json)]
        M[(mocktails.json)]
        S[(substitutions.json)]
        U[(unlock_scores.json)]
    end

    CA --> RDB
    MM --> FP
    RW --> RDB
    RW --> SF
    BA --> UC

    RDB --> C
    RDB --> M
    FP --> C
    FP --> M
    SF --> S
    UC --> U
```

---

## 14. Local Storage Schema

```mermaid
erDiagram
    CABINET {
        string[] ingredients "bourbon, gin, lemons..."
    }

    PREFERENCES {
        string skill_level "beginner|intermediate|adventurous"
        string drink_type "cocktail|mocktail|both"
        int exclude_count "5"
    }

    HISTORY {
        string recipe_id "gold-rush"
        string recipe_name "Gold Rush"
        datetime made_at "2025-12-27T18:30:00Z"
        boolean is_mocktail "false"
    }

    BROWSER ||--o{ CABINET : stores
    BROWSER ||--|| PREFERENCES : stores
    BROWSER ||--o{ HISTORY : stores
```

---

## 15. API Endpoints

```mermaid
flowchart LR
    subgraph Endpoints["FastAPI Routes"]
        recommend["POST /api/recommend"]
        another["POST /api/another"]
        made["POST /api/made"]
        recipe["GET /api/recipe/{id}"]
    end

    subgraph Request1["Recommend Request"]
        r1["cabinet: string[]<br/>mood: string<br/>drink_type: string<br/>skill_level: string<br/>recent_history: string[]"]
    end

    subgraph Request2["Another Request"]
        r2["session_id: string<br/>rejected: string"]
    end

    subgraph Request3["Made Request"]
        r3["recipe_id: string"]
    end

    subgraph Response["Response"]
        resp["recommendation: {...}<br/>alternatives: [...]<br/>next_bottle: {...}<br/>session_id: string"]
    end

    r1 --> recommend
    r2 --> another
    r3 --> made
    recommend --> Response
    another --> Response
```

---

## 16. Directory Structure

```mermaid
flowchart TB
    subgraph Root["cocktail-cache/"]
        subgraph App["app/"]
            main["main.py"]
            config["config.py"]

            subgraph Agents["agents/"]
                ca["cabinet_analyst.py"]
                mm["mood_matcher.py"]
                rw["recipe_writer.py"]
                ba["bottle_advisor.py"]
            end

            subgraph Crews["crews/"]
                ac["analysis_crew.py"]
                rc["recipe_crew.py"]
            end

            subgraph Tools["tools/"]
                rdb["recipe_db.py"]
                fp["flavor_profiler.py"]
                sf["substitution_finder.py"]
                uc["unlock_calculator.py"]
            end

            subgraph Flows["flows/"]
                cf["cocktail_flow.py"]
            end

            subgraph Models["models/"]
                models["cabinet.py<br/>cocktail.py<br/>recipe.py<br/>..."]
            end

            subgraph Templates["templates/"]
                templates["base.html<br/>index.html<br/>components/..."]
            end
        end

        subgraph Data["data/"]
            data["cocktails.json<br/>mocktails.json<br/>ingredients.json<br/>..."]
        end

        subgraph Tests["tests/"]
            tests["features/<br/>steps/<br/>agents/<br/>tools/"]
        end

        Docs["product.md<br/>architecture.md<br/>diagrams.md"]
    end
```

---

*Diagrams Version: 2.0 (Mermaid)*
*Last Updated: 2025-12-27*
