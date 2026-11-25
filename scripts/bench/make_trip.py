"""Gera percursos de teste (NMEA $GPRMC a 1 Hz) que seguem ruas reais, pela rota do OSRM publico.
Uso: python make_trip.py  -> grava app/src/main/assets/debug/trip.nmea e trip-desvio.nmea
Os pontos sao enderecos publicos de Londrina; nada pessoal sai do PC alem das coordenadas."""
import json, math, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'app/src/main/assets/debug'
START = (-51.1630, -23.3105)          # (lon, lat)
DEST = (-51.1561, -23.3040)           # mesmo destino do benchmark (1,4 km)
DETOUR = (-51.1680, -23.3040)         # ponto fora do caminho: forca o recalculo
SPEED = 11.1                          # m/s (~40 km/h)
R = 6371000.0


def osrm(points):
    path = ';'.join('%.6f,%.6f' % p for p in points)
    url = 'https://router.project-osrm.org/route/v1/driving/' + path + '?overview=full&geometries=geojson'
    req = urllib.request.Request(url, headers={'User-Agent': 'HarumiAutoOS-bench/1.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    assert data['code'] == 'Ok', data
    return data['routes'][0]['geometry']['coordinates']


def dist(a, b):
    la1, la2 = math.radians(a[1]), math.radians(b[1])
    dla, dlo = la2 - la1, math.radians(b[0] - a[0])
    x = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(min(1, math.sqrt(x)))


def bearing(a, b):
    la1, la2, dlo = math.radians(a[1]), math.radians(b[1]), math.radians(b[0] - a[0])
    y = math.sin(dlo) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def sample(coords, step):
    """Pontos a cada `step` metros ao longo da polilinha, com rumo do segmento."""
    out, carry = [], 0.0
    for a, b in zip(coords, coords[1:]):
        d = dist(a, b)
        if d < 0.5:
            continue
        brg, s = bearing(a, b), carry
        while s <= d:
            t = s / d
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, brg))
            s += step
        carry = s - d
    out.append((coords[-1][0], coords[-1][1], out[-1][2] if out else 0.0))
    return out


def nmea(points, speed):
    lines = []
    for i, (lon, lat, brg) in enumerate(points):
        stop = i >= len(points) - 3            # parado nos ultimos segundos
        hh, mm, ss = 14, (i // 60) % 60, i % 60
        def dm(v, deg_w):
            v = abs(v); d = int(v); return '%0*d%07.4f' % (deg_w, d, (v - d) * 60)
        body = 'GPRMC,%02d%02d%02d.00,A,%s,%s,%s,%s,%.1f,%.1f,031126,,,A' % (
            hh, mm, ss, dm(lat, 2), 'S' if lat < 0 else 'N', dm(lon, 3), 'W' if lon < 0 else 'E',
            0.0 if stop else speed * 1.943844, brg)
        cs = 0
        for ch in body:
            cs ^= ord(ch)
        lines.append('$%s*%02X' % (body, cs))
    return '\n'.join(lines) + '\n'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    direct = osrm([START, DEST])
    (OUT / 'trip.nmea').write_text(nmea(sample(direct, SPEED), SPEED), encoding='ascii')
    # Desvio: segue o caminho certo no inicio e depois vai para outra rua antes de voltar ao destino.
    detour = osrm([START, DETOUR, DEST])
    (OUT / 'trip-desvio.nmea').write_text(nmea(sample(detour, SPEED), SPEED), encoding='ascii')
    for f in ('trip.nmea', 'trip-desvio.nmea'):
        n = len((OUT / f).read_text().splitlines())
        print(f, n, 'pontos (~%d s)' % n)


if __name__ == '__main__':
    main()
