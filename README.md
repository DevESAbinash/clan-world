# Clan World - AI vs Human decision-making study

An offline pixel game (Python + pygame) for studying how AI models and humans make decisions under risk.
Three modes: **AI vs Human**, **AI vs AI**, **AI vs Hybrid (Human + AI advisor)**.
Every game is logged as data and used to train and compare Logistic Regression, Linear Regression and XGBoost players.

## Quick start (Windows, VS Code, Git Bash)
```bash
python -m venv .venv
source .venv/Scripts/activate        # PowerShell: .venv\Scripts\activate
pip install -r requirements.txt
python train.py                      # train the 3 AI models (few minutes)
python report.py --tournament 20     # AI-vs-AI games -> performance.png
python main.py                       # play (or press F5 in VS Code)
```
After changing any rule in `core.py`, delete the `models` folder and the old `data` logs, then retrain.

## Project structure
| File | Role |
|---|---|
| `core.py` | Game engine and AI brain: rules, constants, `Game`, `Brain`, logging, `stats()` |
| `main.py` | pygame window: menu, map, buttons, vaccine timer, performance graph |
| `train.py` | Generates self-play data, trains logistic / linear / XGBoost, saves to `models/` |
| `report.py` | Optional AI-vs-AI tournament, then draws `performance.png` (matplotlib) |
| `requirements.txt` | pygame, numpy, scikit-learn, xgboost, joblib, matplotlib |
| `.vscode/launch.json` | F5 run/debug configurations |
| `models/` | Trained `.joblib` files (created by `train.py`) |
| `data/` | `human_games.csv`, `ai_games.csv` (decision rows), `results.csv` (one row per player per game) |

## Game rules (all in `core.py`)
- **Time:** 1 turn = 10 s, 12 turns = 1 day (2 min), 40 days max. One action per turn.
- **Coins:** +10 coins every day plus half of unspent coins (savings). Each citizen earns 1 coin/day (Clan 5 earns 0.8).
- **Clans:** 5 numbered clans, 1 coin each. Home capacity is 20 people.
- **Clan resilience** (`RES`): Clan 1 resists Rainstorm / weak to Outbreak; Clan 2 resists Flood / weak to Earthquake; Clan 3 resists Earthquake / weak to Rainstorm; Clan 4 resists Outbreak / weak to Flood; Clan 5 has no weakness.
- **Events** (random victims, resistant clans are half as likely, weak clans twice as likely):

| Event | Deaths | Notes |
|---|---|---|
| Rainstorm | 1 | daily weather per land |
| Earthquake | 2 | random, any turn |
| Flood | 3 | random, any turn |
| Outbreak | 5 | 10 s window to buy vaccines (2 coins each, 1 vaccine saves 1 person) |

- **Free Land:** travel pass costs 20 coins for 5 days. More than 20 people there means one unprotected member dies each day; a shield (5 coins) protects you for the day.
- **Battle:** allowed when Free Land holds more than 20 people; the difference in numbers survives (random survivors).
- **Winning:** hold Free Land with 10+ people while the rival has none for 3 days, otherwise highest `score + 2 x population` on day 40.

## ML design
- **Actions (11):** recruit clan 1-5, explore Free Land, return home, start battle, buy shield, wait, vaccinate.
- **Features (16):** day, coins, own population, rival population, own people in Free Land, rival people in Free Land, travel-pass days, shield, turn, vaccines, outbreak flag, count of each clan (1-5).
- **Models:** logistic predicts P(win); linear and XGBoost predict final score lead. For each legal action the AI scores `features + action one-hot` and plays the best one (5% exploration). `random` is the baseline.
- **Training:** round 1 = random self-play; round 2 = models play each other with exploration; human and AI game logs in `data/*_games.csv` are added. Old-format rows are skipped.

## Controls
| Where | Keys |
|---|---|
| Menu | `1` `2` `3` mode, `A` opponent model, `B` your AI model, `G` performance graph, `ENTER` start |
| Playing | mouse buttons for actions, `SPACE` accept AI advice (mode 3), `UP`/`DOWN` speed, `T` live charts on/off, `G` model graph (pauses game) |
| Outbreak | click **Vaccinate** as many times as you can afford within 10 s |

## Customising (where to edit)
- Prices, capacity, rent, event sizes: constants at the top of `core.py` (`PRICE`, `VAX`, `DEAD`, `CAP`, `LIM`, `RENT`, `TPD`, `MAXDAY`, `CAPT`).
- Clan strengths and income: `RES`, `EARN`.
- Event probabilities: `end_turn()`. Day-end income, overcrowding, win check: `end_day()`.
- Add or change AI inputs: `Game.feat()` (then retrain). New action: extend `ACT`, `valid()` and `act()`.
- Labels and colours: `ACT`, `ZN`, `COL` in `core.py`; layout in `main.py`.

## Build a Windows .exe
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```
Copy the `models` folder next to the exe.

## Troubleshooting
- **Keys do nothing:** click inside the game window first, use the top-row number keys.
- **AI plays randomly:** `models/` is missing or from an older rule set; run `python train.py`.
- **Graph is empty:** finish some games or run `python report.py --tournament 20`.
- **`pip` / `python` not found:** use `py` instead of `python` on Windows.
