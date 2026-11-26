import time
from collections import deque


class _Timeout(Exception):
    """wenn das Zeitlimit der Suche überschritten ist"""
    pass


#Hilfsfunktionen für das CSP
def ueberlappen(p, q):
    """True, wenn zwei Positionen (je ein Tupel aus 2 Feldern) ein Feld teilen
    = Constraint verletzt"""
    return p[0] in q or p[1] in q


def berechne_nachbarn(domains):
    """Zwei Steine sind Nachbarn, wenn ihre Domänen ein gemeinsames Feld enthalten
    Nur für Nachbarn existiert ein relevanter Constraint-Bogen, alle anderen
    Paare können sich nie überlappen und müssen nicht geprüft werden"""
    feld_zu_steinen = {}
    for stein, positionen in domains.items():
        for pos in positionen:
            for feld in pos:
                feld_zu_steinen.setdefault(feld, set()).add(stein)

    nachbarn = {stein: set() for stein in domains}
    for steine in feld_zu_steinen.values():
        for s in steine:
            nachbarn[s] |= steine - {s}
    return nachbarn


#Konsistenztechniken
def knotenkonsistenz(doms):
    """1-Konsistenz: Es gibt keine unären Constraints, die Wertebereiche
    wurden bereits beim CSP-Aufbau auf passende Positionen eingeschränkt
    Es bleibt zu prüfen, dass keine Domäne leer ist"""
    return all(len(d) > 0 for d in doms.values())


def revise(doms, xi, xj):
    """Entfernt alle Positionen aus D(xi), die in D(xj) keinen Partner haben
    (keine Position in D(xj), die nicht überlappt)
    Gibt True zurück, wenn D(xi) verändert wurde"""
    behalten = [p for p in doms[xi]
                if any(not ueberlappen(p, q) for q in doms[xj])]
    geaendert = len(behalten) != len(doms[xi])
    if geaendert:
        doms[xi] = behalten
    return geaendert

def ac3(doms, nachbarn, queue=None, deadline=None):
    """AC3 auf doms (wird in-place verändert)
    queue=None -> alle Bögen (initiale 2-Konsistenz), sonst nur die übergebenen
    deadline -> optionaler Zeitpunkt (perf_counter), danach _Timeout
    Rückgabe: False, wenn eine Domäne leer wird (Inkonsistenz), sonst True"""
    if queue is None:
        queue = deque((xi, xj) for xi in doms for xj in nachbarn[xi])
    else:
        queue = deque(queue)

    schritte = 0
    while queue:
        #Zeitlimit auch innerhalb von AC3 beachten (nur alle 256 Schritte prüfen)
        schritte += 1
        if deadline is not None and schritte % 256 == 0 \
                and time.perf_counter() > deadline:
            raise _Timeout()

        xi, xj = queue.popleft()
        if revise(doms, xi, xj):
            if not doms[xi]:
                return False
            #D(xi) hat sich geändert -> alle Bögen (xk, xi) neu prüfen.
            #(xk, xi) mit xk == xj kann entfallen: Die entfernten Werte aus
            #D(xi) hatten keinen Partner in D(xj), stützten also keinen Wert von xj.
            for xk in nachbarn[xi]:
                if xk != xj:
                    queue.append((xk, xi))
    return True


#Suche
def ac3_suche(domains, zeitlimit=60.0):
    """Suche mit MRV + Gradheuristik; AC3 im Startzustand und nach jeder
    Belegung (MAC = Maintaining Arc Consistency, enthält Forward Checking).
    Rückgabe: dict mit loesung, dauer, belegungen, backtracks, timeout
    (gleiches Format wie fc_ohne_heuristik / fc_mit_heuristik)."""
    start = time.perf_counter()
    deadline = start + zeitlimit
    zaehler = {"belegungen": 0, "backtracks": 0}
    nachbarn = berechne_nachbarn(domains)

    def waehle_variable(doms, belegung):
        #MRV: Stein mit der kleinsten Restdomäne.
        #Tie-Break (Gradheuristik): meiste noch unbelegte Nachbarn.
        return min(
            (s for s in doms if s not in belegung),
            key=lambda s: (len(doms[s]),
                           -sum(1 for n in nachbarn[s] if n not in belegung)),
        )

    def rekursion(doms, belegung):
        if time.perf_counter() > deadline:
            raise _Timeout()
        #alle Steine platziert -> Lösung
        if len(belegung) == len(doms):
            return dict(belegung)

        var = waehle_variable(doms, belegung)
        for wert in doms[var]:
            zaehler["belegungen"] += 1
            #Domänen kopieren, damit Backtracking den Zustand zurücksetzen kann
            neu = {s: list(d) for s, d in doms.items()}
            neu[var] = [wert]
            belegung[var] = wert

            #Propagation ab der belegten Variable: Nachbarn gegen den
            #Singleton prüfen (= Forward Checking), Änderungen kaskadieren
            #automatisch über die Queue (= AC3).
            queue = [(z, var) for z in nachbarn[var]]
            if ac3(neu, nachbarn, queue, deadline):
                ergebnis = rekursion(neu, belegung)
                if ergebnis is not None:
                    return ergebnis

            #Sackgasse (leere Domäne oder Teilbaum ohne Lösung)
            del belegung[var]
            zaehler["backtracks"] += 1
        return None

    loesung, timeout = None, False
    try:
        arbeits_doms = {s: list(d) for s, d in domains.items()}
        #1-Konsistenz, dann 2-Konsistenz im Startzustand
        if knotenkonsistenz(arbeits_doms) and ac3(arbeits_doms, nachbarn,
                                                  deadline=deadline):
            loesung = rekursion(arbeits_doms, {})
    except _Timeout:
        timeout = True

    return {
        "loesung": loesung,
        "dauer": time.perf_counter() - start,
        "belegungen": zaehler["belegungen"],
        "backtracks": zaehler["backtracks"],
        "timeout": timeout,
    }

#Ausgabe und Verifikation der Lösung (Aufgabenblatt, Punkt b)
def pruefe_loesung(gitter, loesung):
    #Unabhängige Kontrolle: jede Position ist benachbart, passt zum Stein, und jedes Feld des Gitters wird genau einmal belegt
    belegt = set()
    for stein, (f1, f2) in loesung.items():
        (i1, j1), (i2, j2) = f1, f2
        if abs(i1 - i2) + abs(j1 - j2) != 1:
            return False
        if tuple(sorted((gitter[i1][j1], gitter[i2][j2]))) != stein:
            return False
        if f1 in belegt or f2 in belegt:
            return False
        belegt.update((f1, f2))
    return len(belegt) == len(gitter) * len(gitter[0])


def formatiere_loesung(gitter, loesung):
    #Gitter mit - und | zwischen Dominohälften
    zeilen, spalten = len(gitter), len(gitter[0])
    breite = len(str(max(max(z) for z in gitter)))
    horizontal, vertikal = set(), set()
    for f1, f2 in loesung.values():
        (i1, j1), (i2, j2) = sorted((f1, f2))
        if i1 == i2:
            horizontal.add((i1, j1))   #Feld (i1,j1) verbunden mit rechtem Nachbarn
        else:
            vertikal.add((i1, j1))     #Feld (i1,j1) verbunden mit unterem Nachbarn

    text = []
    for i in range(zeilen):
        zeile = ""
        for j in range(spalten):
            zeile += str(gitter[i][j]).rjust(breite)
            if j < spalten - 1:
                zeile += "-" if (i, j) in horizontal else " "
        text.append(zeile)
        if i < zeilen - 1:
            trenn = ""
            for j in range(spalten):
                trenn += ("|" if (i, j) in vertikal else " ").rjust(breite)
                if j < spalten - 1:
                    trenn += " "
            text.append(trenn)
    return "\n".join(text)