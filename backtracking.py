import time


class Backtracking:

    def __init__(self, domains, time_limit=60.0):
        self.domains = domains
        self.order = list(domains.keys())      #feste Variablenreihenfolge
        self.time_limit = time_limit
        self.belegt = set()                    #bereits belegte Zellen
        self.zuweisung = {}                    #Stein -> Position
        self.assignments = 0
        self.backtracks = 0
        self.duration = 0.0
        self.timed_out = False
        self.solution = None
        self._deadline = 0.0

    def solve(self):
        start = time.perf_counter()            #Suche startet nach CSP-Aufbau
        self._deadline = start + self.time_limit
        try:
            if self._search(0):
                self.solution = dict(self.zuweisung)
        except TimeoutError:
            self.timed_out = True
        self.duration = time.perf_counter() - start
        return {
            "loesung": self.solution,
            "dauer": self.duration,
            "belegungen": self.assignments,
            "backtracks": self.backtracks,
            "timeout": self.timed_out,
        }

    def _search(self, i):
        if time.perf_counter() > self._deadline:
            raise TimeoutError
        if i == len(self.order):
            return True

        stein = self.order[i]
        for pos in self.domains[stein]:        #feste Wertereihenfolge
            z1, z2 = pos
            if z1 in self.belegt or z2 in self.belegt:   #Constraint: kein Überlapp
                continue

            self.belegt.add(z1)
            self.belegt.add(z2)
            self.zuweisung[stein] = pos
            self.assignments += 1

            if self._search(i + 1):
                return True

            self.backtracks += 1
            self.belegt.discard(z1)
            self.belegt.discard(z2)
            del self.zuweisung[stein]
        return False


def render_solution(gitter, loesung):
    #Gitter mit - und | zwischen Dominohälften
    R, C = len(gitter), len(gitter[0])
    canvas = [[" "] * (2 * C - 1) for _ in range(2 * R - 1)]
    for r in range(R):
        for c in range(C):
            canvas[2 * r][2 * c] = str(gitter[r][c])
    for (r1, c1), (r2, c2) in loesung.values():
        canvas[r1 + r2][c1 + c2] = "-" if r1 == r2 else "|"
    return "\n".join("".join(row) for row in canvas)