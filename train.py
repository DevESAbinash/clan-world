"""Train the AI brains.  Usage: python train.py [games=150] [rounds=2]
Round 1 = random self-play. Round 2 = models play each other (+ exploration).
Also learns from data/*_games.csv written by the game (old-format rows are skipped)."""
import sys, os, glob, csv, random, joblib
import numpy as np
from core import Game, Brain, NA
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

WIDTH = len(Game().feat(0)) + NA + 2


def play(b, eps):
    g = Game()
    while g.winner is None:
        for i in (0, 1): g.act(i, b[i].pick(g, i, eps))
        g.end_turn()
        if g.virus is not None:
            for i in (0, 1): g.ai_vax(i, b[i], eps)
            g.resolve_virus()
    return g.rows()


def fit(R):
    A = np.array(R, float); X, w, d = A[:, :-2], A[:, -2], A[:, -1]
    os.makedirs("models", exist_ok=True)
    M = {"logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X, w),  # P(win)
         "linear": LinearRegression().fit(X, d),                                                    # score lead
         "xgboost": XGBRegressor(n_estimators=150, max_depth=4, learning_rate=.1).fit(X, d)}
    for k, m in M.items(): joblib.dump(m, f"models/{k}.joblib")
    print("trained on", len(A), "rows")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    R = []
    for f in glob.glob("data/*_games.csv"):
        R += [[float(c) for c in r] for r in csv.reader(open(f)) if len(r) == WIDTH]
    for r in range(rounds):
        for k in range(n if r == 0 else n // 3):
            kinds = ["random", "random"] if r == 0 else random.sample(["logistic", "linear", "xgboost", "random"], 2)
            R += play([Brain(kinds[0]), Brain(kinds[1])], .3)
            if (k + 1) % 25 == 0: print(f"round {r+1}: {k+1} games")
        fit(R)
