package com.harumi.autoos.navigation;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.util.Log;
import java.io.File;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Busca de destinos sem Internet no indice busca-brasil.sqlite (FTS4 contentless, gerado por scripts/build_search_index.py).
 * Somente leitura; qualquer falha devolve null e o chamador cai para a busca online.
 */
public final class OfflineSearch {
    private static final String TAG = "HarumiMap";
    static final String FILE_NAME = "busca-brasil.sqlite";
    private static final long RETRY_MISSING_MS = 30_000L;
    private static final int CANDIDATE_CAP = 3000;
    private static final Set<String> STOPWORDS = new HashSet<>(Arrays.asList("de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos", "e"));
    private static final Set<String> UFS = new HashSet<>(Arrays.asList("ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg",
        "pa", "pb", "pr", "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"));

    private final File externalMapas, internalMapas;
    private final Object lock = new Object();
    private SQLiteDatabase db;
    private boolean broken;
    private long lastLookup;

    public OfflineSearch(Context context) {
        File ext = context.getExternalFilesDir(null);
        externalMapas = ext == null ? null : new File(ext, "mapas");   // a pasta e criada pelo OfflineTiles; aqui nao criamos nada
        internalMapas = new File(context.getFilesDir(), "mapas");
    }

    // ---------------------------------------------------------------- logica pura (testada na JVM)

    /** Minusculas, sem acento, so [a-z0-9] separados por um espaco. Igual a norm() do script Python. */
    static String normalize(String s) {
        if (s == null) return "";
        String d = Normalizer.normalize(s.toLowerCase(Locale.ROOT), Normalizer.Form.NFD);
        StringBuilder sb = new StringBuilder(d.length());
        boolean space = true;
        for (int i = 0; i < d.length(); i++) {
            char c = d.charAt(i);
            if ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')) { sb.append(c); space = false; }
            else if (Character.getType(c) == Character.NON_SPACING_MARK) { /* acento: ignora */ }
            else if (!space) { sb.append(' '); space = true; }
        }
        int n = sb.length();
        if (n > 0 && sb.charAt(n - 1) == ' ') sb.setLength(n - 1);
        return sb.toString();
    }

    /** Termos normalizados sem preposicoes de ligacao ("catedral de londrina" -> [catedral, londrina]). */
    static List<String> tokens(String q) {
        List<String> out = new ArrayList<>();
        String n = normalize(q);
        if (n.isEmpty()) return out;
        for (String t : n.split(" ")) if (!t.isEmpty() && !STOPWORDS.contains(t)) out.add(t);
        return out;
    }

    static boolean isUf(String t) { return t != null && UFS.contains(t); }

    /** Consulta FTS4: termos de cidade viram "city:x"; os demais, sem coluna; prefixo no ultimo termo. Vazio se nao ha termo. */
    static String buildMatch(List<String> cityTokens, List<String> terms) {
        StringBuilder sb = new StringBuilder();
        if (cityTokens != null) for (String c : cityTokens) { if (sb.length() > 0) sb.append(' '); sb.append("city:").append(c); }
        for (int i = 0; i < terms.size(); i++) {
            if (sb.length() > 0) sb.append(' ');
            sb.append(terms.get(i));
            if (i == terms.size() - 1) sb.append('*');
        }
        return sb.toString();
    }

    /** Pontuacao: textual (nome igual > comeca com > todos os termos como prefixo de palavra) + importancia + proximidade. */
    static double score(String queryNorm, List<String> terms, String nameNorm, int rank, Double distKm) {
        double s = rank * 0.5;
        if (nameNorm.equals(queryNorm)) s += 40;
        else if (nameNorm.startsWith(queryNorm)) s += 25;
        else if (allPrefixes(terms, nameNorm)) s += 10;
        if (distKm != null) s += 40.0 / (1.0 + distKm / 15.0);
        return s;
    }

    private static boolean allPrefixes(List<String> terms, String nameNorm) {
        String[] words = nameNorm.split(" ");
        for (String t : terms) {
            boolean ok = false;
            for (String w : words) if (w.startsWith(t)) { ok = true; break; }
            if (!ok) return false;
        }
        return true;
    }

    /** Distancia aproximada (equirretangular) em km; boa o bastante para ordenar. */
    static double distKm(double lat1, double lon1, double lat2, double lon2) {
        double dy = (lat1 - lat2) * 111.0;
        double dx = (lon1 - lon2) * 111.0 * Math.cos(Math.toRadians(lat1));
        return Math.sqrt(dx * dx + dy * dy);
    }

    /** Texto mostrado ao usuario (e usado como destino). */
    static String displayName(String name, String kind, String city, String uf) {
        boolean hasCity = city != null && !city.isEmpty();
        boolean hasUf = uf != null && !uf.isEmpty();
        if ("estado".equals(kind)) return name;
        if ("cidade".equals(kind)) return hasUf ? name + " - " + uf : name;
        if ("rua".equals(kind) || "rodovia".equals(kind) || "praça".equals(kind)) {
            if (!hasCity) return name;
            return name + ", " + city + (hasUf ? " - " + uf : "");
        }
        if (!hasCity) return name;
        return name + " — " + city + (hasUf ? ", " + uf : "");
    }

    static String jsonString(String s) {
        StringBuilder sb = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') sb.append('\\').append(c);
            else if (c < 0x20) sb.append(String.format(Locale.ROOT, "\\u%04x", (int) c));
            else sb.append(c);
        }
        return sb.append('"').toString();
    }

    /** Sufixos candidatos a nome de cidade (mais longo primeiro, ate 3 palavras), deixando ao menos 1 termo. */
    static List<List<String>> citySuffixes(List<String> toks) {
        List<List<String>> out = new ArrayList<>();
        for (int k = Math.min(3, toks.size() - 1); k >= 1; k--) out.add(new ArrayList<>(toks.subList(toks.size() - k, toks.size())));
        return out;
    }

    static String join(List<String> l) {
        StringBuilder sb = new StringBuilder();
        for (String s : l) { if (sb.length() > 0) sb.append(' '); sb.append(s); }
        return sb.toString();
    }

    // ---------------------------------------------------------------- acesso ao banco

    private static final class Row {
        long id; String name, kind, city, uf, norm; double lat, lon; int rank; double score;
    }

    private static final String SELECT = "SELECT p.id,p.name,p.kind,p.city,p.uf,p.lat,p.lon,p.rank,p.norm FROM places p "
        + "WHERE p.id IN (SELECT docid FROM busca WHERE busca MATCH ? LIMIT " + CANDIDATE_CAP + ")";

    /** JSON [{"name","lat","lon"}], ordenado por relevancia/proximidade; null se o indice nao existe ou deu erro. */
    public String searchJson(String q, Double lat, Double lon, int limit) {
        try {
            synchronized (lock) {
                SQLiteDatabase d = open();
                if (d == null) return null;
                List<Row> rows = search(d, q, lat, lon, Math.max(1, limit));
                StringBuilder sb = new StringBuilder("[");
                for (int i = 0; i < rows.size(); i++) {
                    Row r = rows.get(i);
                    if (i > 0) sb.append(',');
                    sb.append("{\"name\":").append(jsonString(displayName(r.name, r.kind, r.city, r.uf)))
                      .append(",\"lat\":").append(r.lat).append(",\"lon\":").append(r.lon).append('}');
                }
                return sb.append(']').toString();
            }
        } catch (Throwable t) {
            Log.w(TAG, "busca offline falhou: " + t);
            return null;
        }
    }

    private SQLiteDatabase open() {
        if (db != null) return db;
        if (broken) return null;
        long now = System.currentTimeMillis();
        if (now - lastLookup < RETRY_MISSING_MS && lastLookup != 0) return null;
        lastLookup = now;
        List<File> cands = new ArrayList<>();
        if (externalMapas != null) cands.add(new File(externalMapas, FILE_NAME));
        cands.add(new File(internalMapas, FILE_NAME));
        for (File f : cands) {
            if (!f.isFile() || f.length() == 0) continue;
            try {
                db = SQLiteDatabase.openDatabase(f.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS);
                return db;
            } catch (Throwable t) {
                Log.w(TAG, "indice de busca nao abre: " + f + " " + t);
                broken = true;
                return null;
            }
        }
        return null;
    }

    private List<Row> search(SQLiteDatabase d, String q, Double lat, Double lon, int limit) {
        List<String> toks = tokens(q);
        if (toks.isEmpty()) return new ArrayList<>();
        String ufFilter = null;
        if (toks.size() > 1 && isUf(toks.get(toks.size() - 1))) {
            ufFilter = toks.get(toks.size() - 1);
            toks = new ArrayList<>(toks.subList(0, toks.size() - 1));
        }
        Map<Long, Row> merged = new LinkedHashMap<>();
        boolean filtered = false;
        // "X em/de Cidade": se o final bate com um municipio, filtra por ele; se nada sair, busca sem filtro
        for (List<String> suf : citySuffixes(toks)) {
            List<String[]> cities = cityLookup(d, join(suf), ufFilter);
            if (cities.isEmpty()) continue;
            List<String> terms = toks.subList(0, toks.size() - suf.size());
            collect(d, buildMatch(suf, terms), terms, cities, lat, lon, merged);
            if (!merged.isEmpty()) { filtered = true; break; }
        }
        if (!filtered) {
            if (lat != null && lon != null && toks.size() >= 1) {
                String[] near = nearestCity(d, lat, lon);
                if (near != null) {
                    List<String[]> one = new ArrayList<>();
                    one.add(near);
                    collect(d, buildMatch(Arrays.asList(near[0].split(" ")), toks), toks, one, lat, lon, merged);
                }
            }
            collect(d, buildMatch(null, toks), toks, null, lat, lon, merged);
        }
        List<Row> out = new ArrayList<>(merged.values());
        final boolean fUf = ufFilter != null;
        final String fu = ufFilter;
        if (fUf) { List<Row> keep = new ArrayList<>(); for (Row r : out) if (r.uf != null && r.uf.toLowerCase(Locale.ROOT).equals(fu)) keep.add(r); if (!keep.isEmpty()) out = keep; }
        Collections.sort(out, (a, b) -> Double.compare(b.score, a.score));
        return out.size() > limit ? new ArrayList<>(out.subList(0, limit)) : out;
    }

    /** Municipios de nome normalizado igual; cada item: {norm, UF minusculo}. */
    private List<String[]> cityLookup(SQLiteDatabase d, String normName, String uf) {
        List<String[]> out = new ArrayList<>();
        Cursor c = d.rawQuery("SELECT norm, uf FROM places WHERE kind='cidade' AND norm=?", new String[]{normName});
        try { while (c.moveToNext()) { String u = c.getString(1) == null ? "" : c.getString(1).toLowerCase(Locale.ROOT); if (uf == null || uf.equals(u)) out.add(new String[]{c.getString(0), u}); } }
        finally { c.close(); }
        return out;
    }

    /** Municipio mais proximo do usuario (janela de ~65 km); {norm, uf} ou null. */
    private String[] nearestCity(SQLiteDatabase d, double lat, double lon) {
        Cursor c = d.rawQuery("SELECT norm, uf, lat, lon FROM places WHERE kind='cidade' AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
            new String[]{String.valueOf(lat - 0.6), String.valueOf(lat + 0.6), String.valueOf(lon - 0.6), String.valueOf(lon + 0.6)});
        try {
            String[] best = null; double bd = Double.MAX_VALUE;
            while (c.moveToNext()) {
                double dk = distKm(lat, lon, c.getDouble(2), c.getDouble(3));
                if (dk < bd) { bd = dk; best = new String[]{c.getString(0), c.getString(1) == null ? "" : c.getString(1).toLowerCase(Locale.ROOT)}; }
            }
            return best;
        } finally { c.close(); }
    }

    private void collect(SQLiteDatabase d, String match, List<String> terms, List<String[]> cityFilter, Double lat, Double lon, Map<Long, Row> into) {
        if (match.isEmpty() || terms.isEmpty()) return;
        String qn = join(terms);
        Cursor c = d.rawQuery(SELECT, new String[]{match});
        try {
            while (c.moveToNext()) {
                long id = c.getLong(0);
                if (into.containsKey(id)) continue;
                Row r = new Row();
                r.id = id; r.name = c.getString(1); r.kind = c.getString(2); r.city = c.getString(3); r.uf = c.getString(4);
                r.lat = c.getDouble(5); r.lon = c.getDouble(6); r.rank = c.getInt(7); r.norm = c.getString(8);
                if (cityFilter != null) {      // o FTS casa palavras soltas ("Nova Londrina" casa "londrina"): exige a cidade exata
                    String cn = normalize(r.city); String u = r.uf == null ? "" : r.uf.toLowerCase(Locale.ROOT);
                    boolean ok = false;
                    for (String[] cf : cityFilter) if (cf[0].equals(cn) && cf[1].equals(u)) { ok = true; break; }
                    if (!ok) continue;
                }
                Double dk = (lat != null && lon != null) ? distKm(lat, lon, r.lat, r.lon) : null;
                r.score = score(qn, terms, r.norm, r.rank, dk);
                into.put(id, r);
            }
        } finally { c.close(); }
    }
}
