package com.harumi.autoos.navigation;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.util.Log;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Tiles vetoriais locais (MBTiles, esquema OpenMapTiles). Somente leitura; qualquer falha devolve "sem tile" e o gateway cai para a Internet. */
public final class OfflineTiles {
    private static final String TAG = "HarumiMap";
    static final String FILE_NAME = "brasil.mbtiles";
    private static final long RETRY_MISSING_MS = 30_000L;
    private final File externalMapas, internalMapas;
    private final Object lock = new Object();
    private SQLiteDatabase db;
    private boolean broken;           // arquivo existe mas nao abre: nao tenta de novo
    private long lastLookup;          // ultima busca por arquivo ausente
    private double[] bounds;          // oeste,sul,leste,norte do metadata (ou null)
    private String summary = "indisponivel";

    /** Resultado de uma consulta: data != null achou; failed = erro de leitura (nao tratar como tile vazio). */
    public static final class Lookup {
        public final byte[] data;
        public final boolean failed;
        Lookup(byte[] data, boolean failed) { this.data = data; this.failed = failed; }
    }

    public OfflineTiles(Context context) {
        File ext = context.getExternalFilesDir(null);
        externalMapas = ext == null ? null : new File(ext, "mapas");
        // A pasta precisa ser criada pelo proprio app: criada por outro dono (cabo/adb), o app nao consegue ler o arquivo.
        if (externalMapas != null && !externalMapas.isDirectory() && !externalMapas.mkdirs()) Log.w("HarumiMap", "nao foi possivel criar " + externalMapas);
        internalMapas = new File(context.getFilesDir(), "mapas");
    }

    // ---- logica pura (testada na JVM) ----

    /** MBTiles usa TMS: a linha 0 fica no sul. Converte o y XYZ (norte=0) para tile_row. */
    static int tmsRow(int z, int y) { return (1 << z) - 1 - y; }

    /** Caminhos candidatos, na ordem: pasta externa do app (adb push / USB) e depois a interna. Ignora diretorios nulos. */
    static List<File> candidatePaths(File externalMapas, File internalMapas) {
        List<File> out = new ArrayList<>();
        if (externalMapas != null) out.add(new File(externalMapas, FILE_NAME));
        if (internalMapas != null) out.add(new File(internalMapas, FILE_NAME));
        return out;
    }

    /** Primeiro candidato que e arquivo regular nao vazio, ou null. */
    static File firstExisting(List<File> candidates) {
        for (File f : candidates) if (f != null && f.isFile() && f.length() > 0) return f;
        return null;
    }

    /** "oeste,sul,leste,norte" em graus; null se invalido. */
    static double[] parseBounds(String s) {
        if (s == null) return null;
        String[] p = s.trim().split("\\s*,\\s*");
        if (p.length != 4) return null;
        double[] b = new double[4];
        try { for (int i = 0; i < 4; i++) b[i] = Double.parseDouble(p[i]); } catch (NumberFormatException e) { return null; }
        for (double v : b) if (Double.isNaN(v) || Double.isInfinite(v)) return null;
        if (b[0] >= b[2] || b[1] >= b[3] || b[1] < -90 || b[3] > 90 || b[0] < -180 || b[2] > 180) return null;
        return b;
    }

    static double tileWest(int z, int x) { return x / (double) (1L << z) * 360.0 - 180.0; }
    static double tileNorth(int z, int y) { double n = Math.PI - 2.0 * Math.PI * y / (double) (1L << z); return Math.toDegrees(Math.atan(Math.sinh(n))); }

    /** True se o tile XYZ esta INTEIRO dentro dos bounds. Tile na borda (parcialmente fora) da false: o gateway usa a Internet. */
    static boolean insideBounds(int z, int x, int y, double[] bounds) {
        if (bounds == null || bounds.length != 4 || z < 0 || z > 30 || x < 0 || y < 0 || x >= (1L << z) || y >= (1L << z)) return false;
        double w = tileWest(z, x), e = tileWest(z, x + 1), n = tileNorth(z, y), s = tileNorth(z, y + 1);
        return w >= bounds[0] && e <= bounds[2] && s >= bounds[1] && n <= bounds[3];
    }

    // ---- acesso ao banco ----

    private SQLiteDatabase open() {
        synchronized (lock) {
            if (db != null) return db;
            if (broken) return null;
            long now = System.currentTimeMillis();
            if (lastLookup != 0 && now - lastLookup < RETRY_MISSING_MS) return null;
            lastLookup = now;
            File f = firstExisting(candidatePaths(externalMapas, internalMapas));
            if (f == null) { summary = "arquivo nao encontrado"; return null; }
            try {
                SQLiteDatabase d = SQLiteDatabase.openDatabase(f.getAbsolutePath(), null, SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS);
                try {
                    Map<String, String> md = readMetadata(d);
                    try (Cursor k = d.rawQuery("SELECT 1 FROM tiles LIMIT 1", null)) { k.moveToFirst(); } // valida a tabela uma vez
                    bounds = parseBounds(md.get("bounds"));
                    summary = String.format(Locale.ROOT, "name=%s bounds=%s minzoom=%s maxzoom=%s format=%s file=%s (%d MB)",
                        md.get("name"), md.get("bounds"), md.get("minzoom"), md.get("maxzoom"), md.get("format"), f.getAbsolutePath(), f.length() >> 20);
                    Log.i(TAG, "offline mbtiles: " + summary);
                    if (bounds == null) Log.w(TAG, "offline mbtiles: metadata sem bounds validos; tiles ausentes irao para a Internet");
                    db = d;
                    return d;
                } catch (RuntimeException e) { d.close(); throw e; }
            } catch (RuntimeException e) { // SQLiteException, arquivo corrompido, sem tabela tiles etc.
                broken = true;
                summary = "erro ao abrir: " + e.getClass().getSimpleName();
                Log.w(TAG, "offline mbtiles: nao foi possivel abrir " + f + ": " + e);
                return null;
            }
        }
    }

    private static Map<String, String> readMetadata(SQLiteDatabase d) {
        Map<String, String> m = new HashMap<>();
        try (Cursor k = d.rawQuery("SELECT name, value FROM metadata WHERE name IN ('name','bounds','minzoom','maxzoom','format')", null)) {
            while (k.moveToNext()) m.put(k.getString(0), k.getString(1));
        } catch (RuntimeException e) { Log.w(TAG, "offline mbtiles: metadata ilegivel: " + e); }
        return m;
    }

    /** Chamar fora da thread principal (o WebView ja chama shouldInterceptRequest em thread propria). */
    public Lookup lookup(int z, int x, int y) {
        SQLiteDatabase d = open();
        if (d == null) return new Lookup(null, false);
        try (Cursor k = d.rawQuery("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
                new String[] { Integer.toString(z), Integer.toString(x), Integer.toString(tmsRow(z, y)) })) {
            return new Lookup(k.moveToFirst() ? k.getBlob(0) : null, false);
        } catch (RuntimeException e) {
            Log.w(TAG, "offline mbtiles: erro lendo " + z + "/" + x + "/" + y + ": " + e);
            return new Lookup(null, true);
        }
    }

    /** Bytes do tile (ainda gzip, como no arquivo) ou null se nao houver. */
    public byte[] tile(int z, int x, int y) { return lookup(z, x, y).data; }

    public boolean available() { return open() != null; }

    /** True se o arquivo esta aberto e o tile (ausente) cai dentro dos bounds: tile vazio legitimo (mar etc.). */
    public boolean coversMissing(int z, int x, int y) {
        if (open() == null) return false;
        synchronized (lock) { return insideBounds(z, x, y, bounds); }
    }

    /** Resumo do metadata para diagnostico. */
    public String summary() { open(); synchronized (lock) { return summary; } }
}
