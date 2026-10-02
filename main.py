import sys, pygame
from core import *

pygame.init()
W, H = 960, 800
scr = pygame.display.set_mode((W, H)); pygame.display.set_caption("Clan World - AI vs Human study")
low = pygame.Surface((160, 90))
f = pygame.font.SysFont("consolas", 16); fb = pygame.font.SysFont("consolas", 26, True)
CLR = [(240, 200, 40), (230, 80, 80), (80, 160, 240), (90, 200, 90), (230, 140, 230)]   # clans 1-5
ZONES = [(3, 25), (55, 25), (108, 25)]
KINDS = ["random", "logistic", "linear", "xgboost"]
MODES = ["", "1: AI vs Human", "2: AI vs AI", "3: AI vs Hybrid (Human + AI)"]
TURN, VWIN = 10.0, 10.0   # seconds per turn (12 turns = 1 day = 2 min), vaccine window


def txt(s, x, y, c=(235, 235, 235), font=f): scr.blit(font.render(s, True, c), (x, y))
def rect(a): return pygame.Rect(10 + (a % 4) * 236, 700 + (a // 4) * 32, 226, 26)


def draw(g, mode, sugg, vt):
    low.fill((20, 20, 30))
    for z, (zx, zy) in enumerate(ZONES): pygame.draw.rect(low, tuple(c // 3 for c in COL[g.clim[z]]), (zx, zy, 50, 60))
    if g.flash: z, c = g.flash; zx, zy = ZONES[z]; pygame.draw.rect(low, c, (zx - 1, zy - 1, 52, 62), 2)
    n = [[0, 0, 0], [0, 0, 0]]
    for i in (0, 1):
        for x in g.p[i].ppl:
            z = g.zone(i, x); k = n[i][z]; zx, zy = ZONES[z]; off = 15 if (z == 1 and i == 1) else 0
            pygame.draw.rect(low, CLR[x[0]], (zx + 3 + (k % 10) * 4.5, zy + 3 + off + (k // 10) * 5, 3, 3)); n[i][z] += 1
    scr.blit(pygame.transform.scale(low, (960, 540)), (0, 0))
    for z in range(3): txt(f"{ZN[z]} [{g.clim[z]}]", ZONES[z][0] * 6, 125, COL[g.clim[z]])
    if g.virus is not None:
        pygame.draw.rect(scr, (60, 20, 80), (0, 60, 960, 50))
        aff = any(i == 0 for i, _ in g.members(g.virus)) or mode == 2
        txt(f"OUTBREAK at {ZN[g.virus]}! " + ("Vaccinate now: " if aff else "You are safe: ") + f"{max(vt,0):.0f}s", 150, 70, COL["Outbreak"], fb)
    txt(f"Day {min(g.day, MAXDAY)}/{MAXDAY}  Turn {g.turn+1}/{TPD}  Free Land pop {g.ncom()} (limit {LIM})  Country capacity {CAP}", 10, 548)
    for i in (0, 1):
        p = g.p[i]; who = ["You" if mode != 2 else "AI 1", "AI Rival"][i]
        txt(f"{who}: Coins {p.pts:.1f}  Population {len(p.ppl)}  Total earned {p.score:.0f}  Travel pass {p.rent}d  Shield {'Y' if p.land else 'N'}  Vaccines {p.vax}", 10, 568 + i * 20)
    x = 10
    for k, name in enumerate(["Sunny", "Cloudy", "Rainstorm(-1)", "Flood(-3)", "Earthquake(-2)", "Outbreak(-5)"]):
        txt(name, x, 610, COL[name.split("(")[0]]); x += 10 * len(name) + 14
    for k in range(5): pygame.draw.rect(scr, CLR[k], (700 + k * 50, 612, 12, 12)); txt(str(k + 1), 716 + k * 50, 610)
    if mode == 3 and sugg is not None and g.virus is None: txt(f"AI advisor suggests: {ACT[sugg]}  (SPACE = accept)", 10, 630, (120, 230, 255))
    for k, (m, c) in enumerate(g.msgs[-3:]): txt(m, 10, 650 + k * 16, c)
    if mode != 2:
        for a in range(NA):
            ok = g.valid(0, a) and (g.virus is None or a == 10) and (g.virus is not None or a != 10)
            pygame.draw.rect(scr, ((90, 40, 110) if a == 10 else (60, 90, 60)) if ok else (45, 45, 45), rect(a), border_radius=4)
            txt(ACT[a], rect(a).x + 8, rect(a).y + 4, (255, 255, 255) if ok else (120, 120, 120))
    else: txt("UP/DOWN = speed", 10, 700)


fs = pygame.font.SysFont("consolas", 13)


def line_chart(x, y, w, h, title, series, cols, names, lo, hi, mid=None):
    s = pygame.Surface((w, h), pygame.SRCALPHA); s.fill((10, 12, 20, 215)); scr.blit(s, (x, y))
    pygame.draw.rect(scr, (80, 80, 100), (x, y, w, h), 1)
    scr.blit(fs.render(title, True, (235, 235, 235)), (x + 8, y + 4))
    px, py, pw, ph = x + 8, y + 26, w - 16, h - 34; rng = max(hi - lo, 1e-6)
    if mid is not None: yy = py + ph - (mid - lo) / rng * ph; pygame.draw.line(scr, (90, 90, 110), (px, yy), (px + pw, yy))
    for k, (d, c, nm) in enumerate(zip(series, cols, names)):
        if len(d) > 1: pygame.draw.lines(scr, c, False, [(px + i * pw / (len(d) - 1), py + ph - (v - lo) / rng * ph) for i, v in enumerate(d)], 2)
        if d: scr.blit(fs.render(f"{nm} {d[-1]:.0f}", True, c), (x + w - 240 + k * 120, y + 4))


def charts(hist, mode):
    if not hist: return
    a = [h[0] for h in hist]; b = [h[1] for h in hist]; p = [100 * h[2] for h in hist]
    nm = ["You" if mode != 2 else "AI 1", "AI Rival"]; cols = [(90, 220, 120), (255, 110, 110)]
    line_chart(20, 350, 450, 186, "Performance (score + 2 x population)", [a, b], cols, nm, 0, max(max(a), max(b), 10) * 1.1)
    line_chart(490, 350, 450, 186, "Win probability % (logistic model)", [p, [100 - v for v in p]], cols, nm, 0, 100, 50)


def graph():
    st = stats(); txt("PERFORMANCE: win rate and average score lead", 190, 30, (240, 200, 40), fb)
    for k, nm in enumerate(["Human", "Human + AI", "random", "logistic", "linear", "xgboost"]):
        y = 110 + k * 90; n, wr, ld = st.get(nm, (0, 0, 0))
        txt(f"{nm} ({n} games)", 30, y + 4); pygame.draw.rect(scr, (50, 50, 60), (300, y, 500, 28))
        pygame.draw.rect(scr, (90, 200, 90), (300, y, int(5 * wr), 28)); txt(f"{wr:.0f}%  lead {ld:+.1f}", 810, y + 4)
    txt("More data: python report.py --tournament 20   |   G = back to game (menu: any key)", 30, 700, (170, 170, 170))


def main():
    clock = pygame.time.Clock(); state = "menu"; mode = 1; k0, k1 = 1, 3
    g = None; hist = []; LB = None; showc = True; showg = False; acc = 0; speed = 1; acted = False; sugg = None; B0 = B1 = None; vt = 0; vbought = False
    def snap(): hist.append((g.fscore(0), g.fscore(1), win_prob(g, LB)))
    while True:
        dt = clock.tick(30) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if state == "menu":
                    u = e.unicode.lower()
                    if u in ("1", "2", "3"): mode = int(u)
                    if u == "a": k1 = (k1 + 1) % 4
                    if u == "b": k0 = (k0 + 1) % 4
                    if u == "g": state = "graph"
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        g = Game(); B0, B1 = Brain(KINDS[k0]), Brain(KINDS[k1]); acc = 0; acted = False
                        sugg = B0.pick(g, 0, 0); state = "play"; hist.clear(); LB = Brain("logistic"); snap()
                elif state in ("over", "graph"): state = "menu"
                elif e.key == pygame.K_t: showc = not showc
                elif e.key == pygame.K_g: showg = not showg
                elif e.key == pygame.K_UP: speed = min(32, speed * 2)
                elif e.key == pygame.K_DOWN: speed = max(1, speed // 2)
                elif e.key == pygame.K_SPACE and mode == 3 and not acted and g.virus is None: acted = g.act(0, sugg); snap()
            if e.type == pygame.MOUSEBUTTONDOWN and state == "play" and mode != 2 and not showg:
                if g.virus is not None:
                    if rect(10).collidepoint(e.pos) and g.act(0, 10): vbought = True; snap()
                elif not acted:
                    for a in range(10):
                        if rect(a).collidepoint(e.pos) and g.act(0, a): acted = True; snap()
        scr.fill((12, 12, 18))
        if state == "menu":
            txt("CLAN WORLD", 330, 80, (240, 200, 40), fb)
            for m in (1, 2, 3): txt(("> " if m == mode else "  ") + MODES[m], 280, 160 + m * 30)
            txt(f"[A] Opponent AI model: {KINDS[k1]}", 280, 300); txt(f"[B] Your AI (adv./P1 in mode 2): {KINDS[k0]}", 280, 330)
            for k, t in enumerate(["Clan 1: resists Rainstorm, weak to Outbreak", "Clan 2: resists Flood, weak to Earthquake", "Clan 3: resists Earthquake, weak to Rainstorm", "Clan 4: resists Outbreak, weak to Flood", "Clan 5: no weakness, but earns 0.8 coins/day"]):
                pygame.draw.rect(scr, CLR[k], (150, 480 + k * 24, 12, 12)); txt(t, 172, 477 + k * 24, (200, 200, 200))
            txt("Press 1/2/3 mode, ENTER start, G = performance graph. Run train.py first.", 150, 400, (170, 170, 170))
            txt("1 turn = 10s, 12 turns = 1 day (2 min). Daily allowance 10 coins; half of savings carry over.", 150, 430, (170, 170, 170))
        elif state == "play" and showg: graph()
        elif state == "play":
            end = False
            if g.virus is not None:
                vt -= dt * speed
                if vt <= 0:
                    if mode == 3 and not vbought: g.ai_vax(0, B0)
                    g.resolve_virus(); sugg = B0.pick(g, 0, 0); snap()
            else:
                acc += dt * speed
                if acc >= TURN:
                    acc = 0; g.act(1, B1.pick(g, 1))
                    if mode == 2 or (mode == 3 and not acted): g.act(0, B0.pick(g, 0))
                    acted = False; g.end_turn()
                    if g.virus is not None:
                        vt, vbought = VWIN, False; g.ai_vax(1, B1)
                        if mode == 2: g.ai_vax(0, B0); g.resolve_virus()
                    snap()
                    if g.winner is not None: end = True
                    else: sugg = B0.pick(g, 0, 0)
            if end:
                save_rows("data/ai_games.csv" if mode == 2 else "data/human_games.csv", g.rows())
                log_result(g, ("Human", KINDS[k0], "Human + AI")[mode - 1], KINDS[k1]); state = "over"
            draw(g, mode, sugg, vt)
            if showc: charts(hist, mode)
        elif state == "graph": graph()
        elif state == "over":
            draw(g, mode, None, 0); charts(hist, mode)
            txt(f"GAME OVER - Player {g.winner+1} wins!  (press any key)", 250, 250, (255, 255, 0), fb)
        pygame.display.flip()


main()
