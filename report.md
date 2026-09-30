# Project 1 Report: Intelligent Search Visualizer

> [!IMPORTANT]
> **AUTOGRADER COMPLIANCE INSTRUCTIONS:**
> This report is parsed automatically by the autograder. To ensure you receive full credit for your work:
> 1. **Do not modify** the section headers (`## ...`) or bold field keys (e.g., `**Name:**`, `**Selected Region:**`, `**Live Deployment URL:**`, etc.).
> 2. **Write your answers directly after** the colon `:` of each field, replacing the placeholder text completely (including the outer brackets `[` and `]`).
> 3. **Maintain the file structure**. Changing headers, bold titles, or deleting lines can cause the autograder to miss your responses and award 0 marks.

---

## Student Information 
- **Name:** Patrick
- **UID (netID):** Thomas
- **UIN:** 677959526

---

## Section 1: Selected City Region
- **Selected Region:** Illinois, USA
---

## Section 2: Map Graph Configuration
- **Total Cities Configured:** 22
- **Total Connection Edges:** 35
- **Graph Fully Connected:** Yes

---

## Section 3: Local Verification & Search Algorithms
*Check the algorithms you successfully ran and verified on your local development server by placing an `x` in the brackets (e.g., `[x]`):*
- [x] Breadth-First Search (BFS)
- [x] Depth-First Search (DFS)
- [x] Uniform Cost Search (UCS)
- [x] Iterative Deepening Search (IDS)
- [x] Greedy Best-First Search (Greedy)
- [x] A* Search (A*)

---

## Section 4: Deployed and Presentation Information
- **Deployment Platform:** Render
- **Live Deployment URL:** https://cs411-project1-rxqc.onrender.com
- **Video Presentation Link:** [Provide an accessible link to your 5–7 minute video presentation]

---

## Section 5: Discussion
- **Which search algorithm is best for this route finding problem?** From Rockford IL, to Champaign, IL, A-Star Search is the best search algorithm. All algorithms with their respected costs and paths are list below from best to worst.
*A-Star Search*
Cost: 212.33 miles
Edges: 5
Nodes Expanded: 12
Path: Rockford, IL -> DeKalb, IL -> Aurora, IL -> Joliet, IL -> Kankakee, IL -> Champaign, IL

*UCS*
Cost: 212.33 miles
Edges: 5
Nodes Expanded: 20
Path: Rockford, IL -> DeKalb, IL -> Aurora, IL -> Joliet, IL -> Kankakee, IL -> Champaign, IL

*Greedy Best-First Search*
Cost: 231.07 miles
Edges: 3
Nodes Expanded: 4
Path: Rockford, IL -> Peoria, IL -> Bloomington, IL -> Champaign, IL

*BFS*
Cost: 231.07 miles
Edges: 3
Nodes Expanded: 7
Path: Rockford, IL -> Peoria, IL -> Bloomington, IL -> Champaign, IL

*IDS*
Cost: 231.07 miles
Edges: 3
Nodes Expanded: 31
Path: Rockford, IL -> Peoria, IL -> Bloomington, IL -> Champaign, IL

*DFS*
Cost: 244.87 miles
Edges: 5
Nodes Expanded: 6
Path: Rockford, IL -> DeKalb, IL -> Aurora, IL -> Joliet, IL -> Bloomington, IL -> Champaign, IL

- **Search Efficiency (Nodes expanded/time taken comparison):** The results below are from "benchmark_results.txt" which is the output of "benchmark.py" which was ran locally on my machine. They are listed in decreasing order of time efficiency (so best is first and worst is last).
BFS    Avg Nodes: 6.8  Max Nodes: 19  Time: 4.4 µs
DFS    Avg Nodes: 12.0 Max Nodes: 22  Time: 7.8 µs
UCS    Avg Nodes: 12.0 Max Nodes: 22  Time: 10.1 µs
Greedy Avg Nodes: 4.3  Max Nodes: 11  Time: 11.0 µs
IDS    Avg Nodes: 39.2 Max Nodes: 297 Time: 13.5 µs
A*     Avg Nodes: 6.6  Max Nodes: 19  Time: 14.5 µs

- **Link the idea of search algorithm to today Generative AI.** 
    [Write your answer here]

