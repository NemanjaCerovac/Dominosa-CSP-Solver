
from puzzles import puzzles
from fc1and2 import fc_ohne_heuristik, fc_mit_heuristik
from ac3 import ac3_suche, formatiere_loesung, pruefe_loesung
import backtracking as bt

def erstelle_csp(gitter):
    zeilen = len(gitter)
    spalten = len(gitter[0])

    #alle zeilen gleich lang
    for zeile in gitter:
        if len(zeile) != spalten:
            raise ValueError("fail gitter")

    #größte zahl
    n = max(max(zeile) for zeile in gitter)

    #steine erstellen
    steine = []
    for a in range(n + 1):
        for b in range(a, n + 1):
            steine.append((a, b))

    #anzahl felder passt
    if zeilen * spalten != 2 * len(steine):
        raise ValueError("fail anzahl felder")


    #mögliche position speichern
    domains = {}
    for stein in steine:
        domains[stein] = []
        for i in range(zeilen):
            for j in range(spalten):
                if j + 1 < spalten:
                    a = gitter[i][j]
                    b = gitter[i][j + 1]
                    if tuple(sorted((a, b))) == stein:
                        domains[stein].append(
                            ((i, j), (i, j + 1))
                        )
                if i + 1 < zeilen:
                    a = gitter[i][j]
                    b = gitter[i + 1][j]
                    if tuple(sorted((a, b))) == stein:
                        domains[stein].append(
                            ((i, j), (i + 1, j))
                        )
        if len(domains[stein]) == 0:
            raise ValueError(f"Keine Position für Stein {stein}")
    return domains


def main():
    for nummer, gitter in enumerate(puzzles, start=1):
        print(f"\nPuzzle {nummer}")
        print("-" * 30)

        for zeile in gitter:
            print(zeile)
        domains = erstelle_csp(gitter)

        print("Dominosteine:", len(domains))
        print("Mögliche Positionen:",
              sum(len(d) for d in domains.values()))

        #solver:
        #backtracking:
        solver = bt.Backtracking(domains, time_limit=60.0)
        ergebnis0 = solver.solve()

        print("\nBacktracking (ohne Propagierung, ohne Heuristik):")

        if ergebnis0["timeout"]:
            print("Lösung: keine - Zeitlimit (60 s) erreicht")

        elif ergebnis0["loesung"] is None:
            print("Keine Lösung gefunden")

        else:
            print("Lösung gefunden:", True)
            print("Lösung gültig:", pruefe_loesung(gitter, ergebnis0["loesung"]))

        print("Zeit:", round(ergebnis0["dauer"], 4), "Sekunden")
        print("Belegungen:", ergebnis0["belegungen"])
        print("Backtracks:", ergebnis0["backtracks"])
        print("Timeout:", ergebnis0["timeout"])


        #fc ohne heuristik
        ergebnis1 = fc_ohne_heuristik(domains)

        print("\nFC ohne Heuristik:")
        print("Loesung gefunden:", ergebnis1["loesung"] is not None)
        print("Zeit:", ergebnis1["dauer"])
        print("Belegungen:", ergebnis1["belegungen"])
        print("Backtracks:", ergebnis1["backtracks"])
        print("Timeout:", ergebnis1["timeout"])

        #fc mit heuristik
        ergebnis2 = fc_mit_heuristik(domains)
        print("\nFC mit MRV:")
        print("Loesung gefunden:", ergebnis2["loesung"] is not None)
        print("Zeit:", ergebnis2["dauer"])
        print("Belegungen:", ergebnis2["belegungen"])
        print("Backtracks:", ergebnis2["backtracks"])
        print("Timeout:", ergebnis2["timeout"])

        #ac3: 1-Konsistenz + AC3 (Start und nach jeder Belegung, MAC) + MRV/Grad
        ergebnis3 = ac3_suche(domains)
        print("\nAC3 + MRV/Grad (MAC):")
        print("Loesung gefunden:", ergebnis3["loesung"] is not None)
        print("Zeit:", ergebnis3["dauer"])
        print("Belegungen:", ergebnis3["belegungen"])
        print("Backtracks:", ergebnis3["backtracks"])
        print("Timeout:", ergebnis3["timeout"])
        if ergebnis3["loesung"] is not None:
            print("Loesung gueltig:", pruefe_loesung(gitter, ergebnis3["loesung"]))
            print(formatiere_loesung(gitter, ergebnis3["loesung"]))

if __name__ == "__main__":
    main()
