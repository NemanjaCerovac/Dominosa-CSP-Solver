
import time


def forward_checking(domains, mit_heuristik=False, zeitlimit=60):
    start = time.monotonic()
    steine = list(domains)
    belegungen = 0
    backtracks = 0
    timeout = False

    def suche(belegung, aktuelle_domains):
        nonlocal belegungen, backtracks, timeout

        #Zeitlimit prüfen
        if time.monotonic() - start >= zeitlimit:
            timeout = True
            return None

        #Alle steine platziert
        if len(belegung) == len(steine):
            return belegung.copy()

        #ächsten Stein auswählen
        if mit_heuristik:
            stein = min(
                (s for s in steine if s not in belegung),
                key=lambda s: len(aktuelle_domains[s])
            )
        else:
            stein = next(s for s in steine if s not in belegung)

        #mögliche Positionen probieren
        for position in aktuelle_domains[stein]:
            if time.monotonic() - start >= zeitlimit:
                timeout = True
                return None

            belegungen += 1
            belegung[stein] = position

            #Domains kopieren
            neue_domains = {
                s: werte.copy()
                for s, werte in aktuelle_domains.items()
            }

            belegte_felder = set(position)
            moeglich = True

            #forward checking
            for anderer in steine:
                if time.monotonic() - start >= zeitlimit:
                    timeout = True
                    del belegung[stein]
                    return None

                if anderer in belegung:
                    continue

                #überlappende Positionen entfernen
                neue_domains[anderer] = [
                    p for p in neue_domains[anderer]
                    if p[0] not in belegte_felder
                    and p[1] not in belegte_felder
                ]

                #keine Position mehr möglich
                if not neue_domains[anderer]:
                    moeglich = False
                    break

            #weitersuchen
            if moeglich:
                loesung = suche(belegung, neue_domains)

                if loesung is not None:
                    return loesung

                if timeout:
                    del belegung[stein]
                    return None

            #backtracking
            del belegung[stein]
            backtracks += 1

        return None

    #Suche starten
    neue_domains = {
        s: werte.copy()
        for s, werte in domains.items()
    }

    loesung = suche({}, neue_domains)
    dauer = time.monotonic() - start

    return {
        "loesung": loesung,
        "dauer": dauer,
        "belegungen": belegungen,
        "backtracks": backtracks,
        "timeout": timeout
    }


def fc_ohne_heuristik(domains, zeitlimit=60):
    return forward_checking(domains, False, zeitlimit)


def fc_mit_heuristik(domains, zeitlimit=60):
    return forward_checking(domains, True, zeitlimit)
