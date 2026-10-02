"""python report.py [--tournament N]  -> AI-vs-AI games for every model pair, then saves performance.png"""
import sys
import matplotlib.pyplot as plt
from core import *

KINDS = ["random", "logistic", "linear", "xgboost"]


def game(b0, b1):
    g = Game()
    while g.winner is None:
        for i, b in enumerate((b0, b1)): g.act(i, b.pick(g, i))
        g.end_turn()
        if g.virus is not None: g.ai_vax(0, b0); g.ai_vax(1, b1); g.resolve_virus()
    return g


if __name__ == "__main__":
    if "--tournament" in sys.argv:
        n = int(sys.argv[sys.argv.index("--tournament") + 1])
        for a in KINDS:
            for b in KINDS:
                if a != b:
                    for _ in range(n): log_result(game(Brain(a), Brain(b)), a, b)
                    print("done", a, "vs", b)
    st = stats(); names = [k for k in ["Human", "Human + AI"] + KINDS if k in st]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].bar(names, [st[k][1] for k in names], color="tab:green"); ax[0].set_title("Win rate (%)"); ax[0].axhline(50, ls="--", c="gray")
    ax[1].bar(names, [st[k][2] for k in names], color="tab:blue"); ax[1].set_title("Average score lead")
    for a in ax: a.tick_params(axis="x", rotation=30)
    plt.tight_layout(); plt.savefig("performance.png", dpi=150); print("saved performance.png"); plt.show()
