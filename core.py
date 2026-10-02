import random, csv, os
import numpy as np

PRICE, VAX = 1, 2                      # every clan costs 1 point, vaccine 2 points
ACT = ["Recruit Clan 1 (-1)", "Recruit Clan 2 (-1)", "Recruit Clan 3 (-1)", "Recruit Clan 4 (-1)", "Recruit Clan 5 (-1)",
       "Explore Free Land (pass 20)", "Return home", "Start battle", "Buy shield (-5)", "Wait", "Vaccinate (-2)"]
NA = len(ACT)
CLIM = ["Sunny", "Cloudy", "Rainstorm"]
COL = {"Sunny": (230, 200, 60), "Cloudy": (150, 150, 165), "Rainstorm": (70, 120, 230),
       "Flood": (30, 210, 220), "Earthquake": (210, 120, 40), "Outbreak": (180, 70, 220)}
DEAD = {"Rainstorm": 1, "Flood": 3, "Earthquake": 2, "Outbreak": 5}   # people who die per event
# clan resilience: multiplier on the chance of being chosen as a victim (0.5 = resistant, 2 = weak)
RES = [{"Rainstorm": .5, "Outbreak": 2}, {"Flood": .5, "Earthquake": 2}, {"Earthquake": .5, "Rainstorm": 2},
       {"Outbreak": .5, "Flood": 2}, {}]
EARN = [1, 1, 1, 1, .8]   # clan 5 is the safe all-rounder but earns a bit less
ZN = ["Home 1", "Free Land", "Home 2"]
TPD, MAXDAY, CAP, LIM, RENT, CAPT = 12, 40, 20, 20, 20, 10   # turns/day, days, country capacity, common limit, rent, capture size


class P:
    def __init__(s):
        s.pts = 10.; s.ppl = []; s.rent = 0; s.land = False; s.score = 0.; s.vax = 0


class Game:
    def __init__(s):
        s.p = [P(), P()]; s.day = 1; s.turn = 0; s.winner = None; s.cap = [0, 0]
        s.msgs = []; s.log = []; s.virus = None; s.flash = None; s.roll()

    def roll(s):
        s.clim = [random.choice(CLIM) for _ in range(3)]   # P1 land, Common, P2 land
        for z in range(3):
            if s.clim[z] == "Rainstorm": s.hit(z, "Rainstorm")

    def say(s, t, c=(255, 200, 120)): s.msgs = (s.msgs + [(f"D{s.day}: {t}", c)])[-6:]
    def zone(s, i, x): return 1 if x[1] else 2 * i
    def members(s, z): return [(i, x) for i in (0, 1) for x in s.p[i].ppl if s.zone(i, x) == z]
    def kill(s, i, x): s.p[i].ppl = [y for y in s.p[i].ppl if y is not x]
    def ncom(s): return sum(1 for p in s.p for x in p.ppl if x[1])
    def fscore(s, i): return s.p[i].score + 2 * len(s.p[i].ppl)

    def choose(s, m, n, name):
        m = list(m); v = []
        for _ in range(min(n, len(m))):
            k = random.choices(range(len(m)), [RES[x[0]].get(name, 1) for _, x in m])[0]; v.append(m.pop(k))
        return v

    def hit(s, z, name):
        m = s.members(z); v = s.choose(m, DEAD[name], name)
        for i, x in v: s.kill(i, x)
        s.flash = (z, COL[name])
        if m: s.say(f"{name.upper()} in {ZN[z]}: {len(v)} died", COL[name])

    def feat(s, i):
        me, op = s.p[i], s.p[1 - i]
        c = [sum(1 for x in me.ppl if x[0] == k) for k in range(5)]
        return [s.day, me.pts, len(me.ppl), len(op.ppl), sum(x[1] for x in me.ppl), sum(x[1] for x in op.ppl),
                me.rent, int(me.land), s.turn, me.vax, int(s.virus is not None)] + c

    def valid(s, i, a):
        p = s.p[i]
        if a < 5: return p.pts >= PRICE and sum(1 for x in p.ppl if not x[1]) < CAP
        if a == 5: return any(not x[1] for x in p.ppl) and (p.rent > 0 or p.pts >= RENT)
        if a == 6: return any(x[1] for x in p.ppl)
        if a == 7: return s.ncom() > LIM and any(x[1] for x in p.ppl) and any(x[1] for x in s.p[1 - i].ppl)
        if a == 8: return p.pts >= 5 and not p.land
        if a == 10: return s.virus is not None and p.pts >= VAX and p.vax < sum(1 for k, _ in s.members(s.virus) if k == i)
        return True

    def act(s, i, a):
        if not s.valid(i, a): return False
        p = s.p[i]
        s.log.append((i, s.feat(i) + [int(a == k) for k in range(NA)]))
        if a < 5: p.pts -= PRICE; p.ppl.append([a, 0])
        elif a == 5:
            if p.rent == 0: p.pts -= RENT; p.rent = 5
            go = [x for x in p.ppl if not x[1]][:5]
            for x in go: x[1] = 1
            s.say(f"Player {i+1} explored Free Land with {len(go)}")
        elif a == 6:
            for x in p.ppl: x[1] = 0
        elif a == 7: s.war()
        elif a == 8: p.pts -= 5; p.land = True
        elif a == 10: p.pts -= VAX; p.vax += 1
        return True

    def war(s):
        c = [[x for x in s.p[k].ppl if x[1]] for k in (0, 1)]
        a, b = len(c[0]), len(c[1]); w = 0 if a >= b else 1
        keep = {id(y) for y in random.sample(c[w], abs(a - b))}
        for k in (0, 1): s.p[k].ppl = [x for x in s.p[k].ppl if not x[1] or (k == w and id(x) in keep)]
        s.say(f"BATTLE {a} vs {b}: {abs(a-b)} survive", (255, 80, 80))

    def ai_vax(s, i, brain, eps=.05):
        for _ in range(8):
            if not s.valid(i, 10) or brain.pick(s, i, eps, only=[9, 10]) == 9: break
            s.act(i, 10)

    def resolve_virus(s):
        z = s.virus
        if z is None: return
        s.virus = None; m = s.members(z); v = s.choose(m, DEAD["Outbreak"], "Outbreak"); dead = 0
        for i, x in v:
            if s.p[i].vax > 0: s.p[i].vax -= 1
            else: s.kill(i, x); dead += 1
        for p in s.p: p.vax = 0
        s.flash = (z, COL["Outbreak"]); s.say(f"OUTBREAK result: {dead} died, {len(v)-dead} saved by vaccine", COL["Outbreak"])

    def end_turn(s):
        s.flash = None
        for z in range(3):
            r = random.random()
            if r < .02: s.hit(z, "Flood")
            elif r < .035: s.hit(z, "Earthquake")
            elif r < .05 and s.virus is None:
                s.virus = z; s.flash = (z, COL["Outbreak"])
                s.say(f"OUTBREAK at {ZN[z]}! 5 at risk - vaccinate now (2 coins each)", COL["Outbreak"])
        s.turn += 1
        if s.turn >= TPD: s.end_day()

    def end_day(s):
        for i, p in enumerate(s.p):
            hn = 0
            for x in p.ppl:                      # every person earns 1 point per day
                if not x[1]:
                    hn += 1
                    if hn > CAP: continue
                p.pts += EARN[x[0]]; p.score += EARN[x[0]]
        com = [(i, x) for i in (0, 1) for x in s.p[i].ppl if x[1]]
        if len(com) > LIM:
            un = [(i, x) for i, x in com if not s.p[i].land]
            if un:
                i, x = random.choice(un); s.kill(i, x); s.say(f"Overcrowding: Player {i+1} lost a member")
        for i, p in enumerate(s.p):
            p.rent = max(0, p.rent - 1)
            if p.rent == 0:
                for x in p.ppl: x[1] = 0
            p.land = False; p.pts = 10 + p.pts / 2
            c = sum(1 for x in p.ppl if x[1]); o = sum(1 for x in s.p[1 - i].ppl if x[1])
            s.cap[i] = s.cap[i] + 1 if c >= CAPT and o == 0 else 0
        s.day += 1; s.turn = 0; s.roll()
        for i in (0, 1):
            if s.cap[i] >= 3: s.winner = i; s.say(f"Player {i+1} captured Free Land!")
        if s.day > MAXDAY and s.winner is None: s.winner = 0 if s.fscore(0) >= s.fscore(1) else 1

    def rows(s):
        f = [s.fscore(0), s.fscore(1)]
        return [x + [int(s.winner == i), f[i] - f[1 - i]] for i, x in s.log]


def save_rows(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", newline="") as fh: csv.writer(fh).writerows(rows)


def log_result(g, t0, t1):
    f = [g.fscore(0), g.fscore(1)]
    save_rows("data/results.csv", [[t0, t1, int(g.winner == 0), f[0] - f[1]], [t1, t0, int(g.winner == 1), f[1] - f[0]]])


def stats():
    d = {}
    try: rows = list(csv.reader(open("data/results.csv")))
    except Exception: return {}
    for t, o, w, l in rows:
        a = d.setdefault(t, [0, 0, 0.]); a[0] += 1; a[1] += int(w); a[2] += float(l)
    return {t: (n, 100 * w / n, l / n) for t, (n, w, l) in d.items()}


def win_prob(g, br):
    """P(player 1 wins) from the logistic model: best legal action value per player, normalised. Falls back to score share."""
    f0, f1 = g.fscore(0), g.fscore(1)
    if br is None or br.m is None or not hasattr(br.m, "predict_proba"): return f0 / (f0 + f1) if f0 + f1 > 0 else .5
    pw = []
    try:
        for i in (0, 1):
            f = g.feat(i); v = [a for a in range(NA) if g.valid(i, a)]
            pw.append(float(br.m.predict_proba(np.array([f + [int(a == k) for k in range(NA)] for a in v], float))[:, 1].max()))
    except Exception: return .5
    return pw[0] / (pw[0] + pw[1]) if pw[0] + pw[1] > 0 else .5


class Brain:
    """kind: random | logistic | linear | xgboost  (models trained by train.py)"""
    def __init__(s, kind="random"):
        s.kind, s.m = kind, None
        if kind != "random":
            try:
                import joblib; s.m = joblib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", kind + ".joblib"))
            except Exception: s.m = None

    def pick(s, g, i, eps=.05, only=None):
        v = [a for a in (only or range(NA)) if g.valid(i, a)] or [9]
        if s.m is None or random.random() < eps: return random.choice(v)
        try:
            f = g.feat(i)
            X = np.array([f + [int(a == k) for k in range(NA)] for a in v], float)
            y = s.m.predict_proba(X)[:, 1] if hasattr(s.m, "predict_proba") else s.m.predict(X)
            return v[int(np.argmax(y))]
        except Exception: return random.choice(v)   # old/mismatched model -> retrain
