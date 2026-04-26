# Emergency Aid Optimizer — Final Project CMPSC 463

This project started from a simple question: how do you decide which people get help first when you don't have enough trucks, supplies, or time for everyone?

We built a web-based tool that models exactly that problem; a dispatcher trying to route aid convoys across a conflict zone, with limited fleet capacity, incomplete information about which roads are passable, and urgency levels that keep rising the longer zones go unserved. The algorithms under the hood are ones we studied this semester, applied to a scenario where the stakes actually matter.

---

## How to run it

You need Python 3 and Flask. That's it.

```bash
pip install flask
python api_server.py
```

It opens automatically at `http://localhost:5000`. If it doesn't, just navigate there manually.

If you want to test the algorithms in the terminal without the GUI, the original `main.py` still works:

```bash
python main.py
```

---

## How to use the GUI

The interface is divided into three panels around a central map. Here's how everything works.

### Left panel - controls

**Scenario selector** picks which crisis you're modeling. Each scenario loads a different set of zones, a different depot location, and different default fleet settings. The description under the buttons tells you what kind of crisis it is and what the dominant challenge is.

**Fleet config** has two sliders. "Trucks" controls how many convoy vehicles you have available — drag it down and watch coverage drop on the next run. "Capacity (kg)" sets how much each truck can carry. Lowering this forces the algorithm to leave more zones unserved because individual zones exceed truck capacity.

**Time simulation** is for the urgency decay feature. Set the "hours per tick" slider, then click **ADVANCE TIME** to simulate the passage of time. Every unserved zone gains urgency the longer it waits, which changes the algorithm's priority order on the next run. Click **RESET TIME** to restore the scenario to its original urgency values.

**Zones list** shows every zone in the current scenario with its urgency rating and demand. Click any zone to block it, it turns red and gets excluded from the next optimizer run. This simulates a road closure or security incident making a zone unreachable. Zones marked with a ? are fog-of-war zones (see below).

### Center - the map

The map uses real geographic coordinates. You can zoom, pan, and click any marker for details.

**Depot** is the gold square label, the origin point for all trucks. All routes start and end here.

**Zone markers** are colored circles. Red means urgency 8–10, orange is 5–7, and blue is 1–4. The circle size also scales with urgency so the most critical zones are visually dominant. A small urgency bar underneath each marker shows how critical the zone is relative to the maximum.

**Purple ? markers** are fog-of-war zones: their accessibility is unknown before a run. Click **REVEAL FOG ZONES** to discover them. Each has a random chance of being accessible or blocked by conditions on the ground. If blocked, they get added to the exclusion list automatically.

**Routes** appear as colored lines after you run the optimizer. Each truck gets a distinct color. The lines trace the exact nearest-neighbor path: depot -> zone -> zone -> depot. Click a route line to see which truck it belongs to and its total distance.

**Running the optimizer** - press the **RUN OPTIMIZER** button to kick off both algorithms simultaneously. After a run, if you've blocked zones or revealed fog zones, the **RE-PLAN** button appears to re-run with updated inputs.

**Algorithm tabs** at the top of the map let you switch between viewing the Greedy result, the Priority Queue result, or both maps side by side. In side-by-side mode, the maps are linked — panning one pans the other.

### Right panel - results

**The two-column metrics** compare Greedy (gold) vs. Priority Queue (blue) directly. Coverage percentage, total aid delivered in tonnes, combined urgency score of served zones, and total fleet travel hours are shown for both algorithms simultaneously.

**The winner badge** below the metrics declares which algorithm came out ahead for that run or calls it a tie if the difference is negligible. The winner is determined by combining coverage percentage and urgency score served.

**Supply breakdown** shows a bar chart of how the greedy fleet's total load breaks down across food, medicine, and shelter kits. This reflects the per-zone supply type data built into each scenario.

**Live counters** tick upward during a run, showing kilometers dispatched, hours en-route, and zones confirmed as they accumulate, rather than just jumping to the final number.

**Truck assignments** shows one card per truck, color-matched to the map. Each card shows which zones that truck was assigned, the route order, total distance, estimated hours, and the supply breakdown it's carrying.

**Activity log** at the bottom records everything: algorithm runs, zone blocking, fog reveals, time ticks, and truck assignments. Most recent entries appear at the top.

### A full demo walkthrough

1. Select **Aleppo Siege** from the scenario list
2. Notice the two purple ? markers on the map - those are fog zones
3. Press **RUN OPTIMIZER** and watch the routes animate
4. Compare Greedy vs. Priority Queue in the metrics - note which served higher urgency zones
5. Click **REVEAL FOG ZONES** - one will be accessible, one blocked
6. Press **RE-PLAN** to update routes around the blocked zone
7. Click a high-urgency zone in the left panel to block it, then RE-PLAN again
8. Switch to **SIDE BY SIDE** tab to compare both algorithm maps at once
9. Set the time slider to 24h and click **ADVANCE TIME** - watch urgency rise on unserved zones
10. Press **RUN OPTIMIZER** again to see how changed urgencies affect assignments

---

## File breakdown

```
├── greedy_select.py        # Scores zones by urgency / (distance × risk), assigns to trucks greedily
├── delivery_optimizer.py   # Nearest-neighbor routing per truck, returns km and estimated hours
├── algorithms.py           # Priority queue (min-heap) algorithm, urgency decay, fog-of-war reveal
├── main.py                 # Standalone terminal demo (runs greedy + re-plan scenario, prints output)
├── GUI/
│   ├── index.html          # The full frontend - Leaflet map, comparison panel, all interactivity
│   └── api_server.py           # Flask server - connects the algorithms to the GUI via REST endpoints
└── README.md
```

---

## Why we chose these four scenarios

We wanted scenarios that were geographically real, algorithmically interesting in different ways, and represented different types of humanitarian crises — not just the same problem with different numbers. Each one was chosen because it stresses the algorithm differently.

### Aleppo Siege - Northern Syria

The siege of eastern Aleppo from 2016 is one of the most documented urban humanitarian disasters of the past decade. After Syrian government forces cut off the last road into rebel-held eastern Aleppo in July 2016, an estimated 250,000 to 300,000 civilians were trapped, with aid agencies reporting that roughly a third of them depended directly on outside assistance. Only 40 doctors remained in the eastern part of the city at the height of the siege. Food prices spiked dramatically and medical supplies ran critically low, with humanitarian organizations describing conditions as deteriorating by the day.

What made Aleppo algorithmically interesting to us was the extreme combination of high urgency and high risk in the same locations. The zones closest to the front lines had the most desperate need but the highest danger scores. Our scoring formula, urgency divided by distance times risk, creates genuine tension here: does the algorithm send a truck into a high-risk corridor to reach the most critical zone, or does it serve a safer zone with slightly lower urgency first? The greedy and priority queue algorithms make different choices, and the difference is most visible in this scenario. We also placed fog-of-war zones here because, in the real Aleppo situation, aid organizations frequently did not know in advance whether a given route or neighborhood was accessible on any given day.

### Idlib Displacement - Northwest Syria

By early 2020, Idlib had become what UN relief chief Mark Lowcock called the site of the worst humanitarian disaster of the century. A military offensive beginning in late 2019 displaced nearly one million people in roughly three months, a scale the UN described as the largest mass displacement since the Syrian conflict began in 2012. Over 80 percent of those displaced were women and children. The Bab al-Hawa border crossing with Turkey was the only authorized entry point for UN humanitarian aid into the region, making depot placement and routing constraints uniquely acute.

We chose Idlib because it represents a different type of crisis from Aleppo; mass displacement rather than urban siege. The dominant need here is shelter, not medicine, which is reflected in the supply type breakdown for this scenario. The depot is placed at the Bab al-Hawa crossing, which is where real aid organizations actually staged their convoys. With several hundred thousand newly displaced people spread across a relatively large geographic area, the nearest-neighbor routing algorithm has to make real trade-offs between serving closer, lower-urgency camps or making longer runs to reach the most desperate zones near the front lines.

### Bekaa Valley Flood - Eastern Lebanon

Lebanon's Bekaa Valley has been one of the most strained humanitarian zones in the region for years, hosting large concentrations of Syrian refugees who were themselves already displaced from the conflict across the border. The valley has historically been described as deprived compared to coastal Lebanon, with residents heavily dependent on outside aid even in normal times. UNHCR noted after the 2006 conflict that it was one of the few organizations to actually follow through on aid delivery to the region, with local coordinators expressing uncertainty about whether help would ever arrive.

We chose the Bekaa scenario because it introduces a different risk profile, the danger here comes from floods and infrastructure instability rather than direct conflict, meaning risk scores are generally lower but road passability is genuinely uncertain. This is where the fog-of-war mechanic is most realistic: in a flood situation, you genuinely don't know if a road has washed out until a truck tries to use it. The scenario also tests the supply type logic specifically shelter kits and food dominate over medicine here, which shifts the algorithm's loading decisions compared to Aleppo.

### Mosul Post-Conflict - Northern Iraq

The battle to retake Mosul from ISIS lasted nine months, from October 2016 to July 2017, and was described as the longest urban battle since World War II. When it ended, an estimated 65 percent of Mosul's historic district had been destroyed, more than 138,000 homes were damaged or demolished, and close to one million people had been displaced. The UN's 2017 Humanitarian Response Plan described it as potentially the single largest humanitarian operation in the world that year. Two years after the city was declared liberated, 300,000 people from the district were still unable to return home and the reconstruction plan was less than half funded.

Mosul represents a different phase of crisis entirely; post-conflict reconstruction rather than active conflict response. Aid still needs to move through a city full of unexploded ordnance, contested neighborhoods, and damaged infrastructure, but the urgency profile is more varied than in active siege scenarios. Some zones have extreme medical need from ongoing trauma injuries; others need food or shelter for families trying to return to ruined homes. We chose Mosul because it has the most zones of any scenario and the most mixed risk and urgency values, which gives the algorithm comparison the most interesting results, greedy and priority queue tend to diverge more here than in any other scenario.

---

## The algorithms

**Greedy selection** (`greedy_select.py`) - every zone gets a priority score: `urgency / (distance × risk)`. Higher urgency gets you served sooner. Higher distance or risk drops your score. Zones are sorted by score and assigned to the first truck that has capacity, working down the list. Fast and intuitive, but locally optimal decisions aren't always globally optimal.

**Priority queue dispatch** (`algorithms.py`) - same scoring formula, but implemented with Python's `heapq` module as a min-heap. The key difference is assignment strategy: the PQ approach always sends the highest-scoring remaining zone to whichever truck has the most remaining capacity, rather than filling trucks sequentially. On some scenarios this produces better urgency coverage; on others greedy wins. The comparison panel shows you which came out ahead.

**Nearest-neighbor routing** (`delivery_optimizer.py`) - once zones are assigned to a truck, we need an order to visit them. This is the Travelling Salesman Problem, which is NP-hard for exact solutions. We use the nearest-neighbor heuristic: start at the depot, always drive to the closest unvisited zone, repeat until done, then return to depot. Not guaranteed optimal but runs instantly.

**Urgency decay** (`algorithms.py`) - every time you advance the clock, unserved zones gain 0.3 urgency points per simulated hour, capped at 10. This models the reality that waiting makes things worse and forces the optimizer to reprioritize on each tick.

**Fog of war** (`algorithms.py`) - some zones are marked unknown before a run. When revealed, each has a 65% chance of being accessible and 35% of being blocked. Blocked fog zones get added to the exclusion list and the optimizer re-plans automatically.

---
