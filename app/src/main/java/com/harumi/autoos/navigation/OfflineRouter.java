package com.harumi.autoos.navigation;
import android.content.Context;
import android.util.Log;
import com.graphhopper.GHRequest;
import com.graphhopper.GHResponse;
import com.graphhopper.GraphHopper;
import com.graphhopper.GraphHopperConfig;
import com.graphhopper.ResponsePath;
import com.graphhopper.config.CHProfile;
import com.graphhopper.util.Instruction;
import com.graphhopper.util.InstructionList;
import com.graphhopper.util.PointList;
import com.graphhopper.util.RoundaboutInstruction;
import com.harumi.autoos.navigation.gh.HarumiGraphHopper;
import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Locale;

/**
 * Roteador local (GraphHopper, perfil "car" com CH) usado quando a Internet falha.
 * O grafo e gerado no PC e copiado para getExternalFilesDir/rotas/grafo-brasil-v2 (ver docs/MAPA-OFFLINE.md).
 * Carrega uma unica vez, em segundo plano, em modo MMAP somente leitura. Devolve JSON no formato OSRM.
 */
public final class OfflineRouter {
    private static final String TAG = "HarumiRoute";
    private final File graphDir;
    private GraphHopper hopper;      // guardado por this
    private boolean failed;          // guardado por this: erro de carga que nao adianta repetir
    private boolean warming;         // guardado por this

    public OfflineRouter(Context context) {
        File root = context.getExternalFilesDir(null);
        if (root == null) root = context.getFilesDir();
        File rotas = new File(root, "rotas");
        rotas.mkdirs(); // criada pelo proprio app: pasta criada por adb antes dele fica sem permissao de leitura
        graphDir = new File(rotas, "grafo-brasil-v2");
        graphDir.mkdirs(); // idem: o app cria tambem a pasta do grafo, e o adb so copia os arquivos para dentro dela
    }

    /** True se a pasta do grafo existe e tem o arquivo de propriedades do GraphHopper. */
    public boolean available() {
        return !isFailed() && new File(graphDir, "properties").isFile();
    }

    private synchronized boolean isFailed() { return failed; }

    /** Inicia a carga do grafo em segundo plano (uma vez). Nao faz nada se nao houver grafo. */
    public void warmUp() {
        synchronized (this) { if (warming || hopper != null || failed) return; warming = true; }
        if (!new File(graphDir, "properties").isFile()) { synchronized (this) { warming = false; } return; }
        Thread t = new Thread(() -> {
            try { load(); } catch (IOException ignored) { } finally { synchronized (this) { warming = false; } }
        }, "offline-router-load");
        t.setDaemon(true);
        t.setPriority(Thread.MIN_PRIORITY + 1);
        t.start();
    }

    private synchronized GraphHopper load() throws IOException {
        if (hopper != null) return hopper;
        if (failed) throw new IOException("Offline router unavailable");
        if (!new File(graphDir, "properties").isFile()) throw new IOException("Offline graph not found");
        long t0 = System.nanoTime();
        try {
            GraphHopperConfig cfg = new GraphHopperConfig();
            cfg.putObject("graph.location", graphDir.getAbsolutePath());
            cfg.putObject("graph.dataaccess.default_type", "MMAP_RO");
            cfg.putObject("graph.encoded_values", "car_access, car_average_speed, road_access");
            cfg.putObject("import.osm.ignored_highways", "footway,construction,cycleway,path,steps"); // exigido pelo init(); sem efeito ao so ler o grafo
            cfg.putObject("prepare.min_network_size", 200);
            cfg.putObject("routing.snap_preventions_default", "tunnel, bridge, ferry");
            cfg.setProfiles(List.of(HarumiGraphHopper.carProfile())); // peso proprio, sem Janino (que nao roda no Android)
            cfg.setCHProfiles(List.of(new CHProfile("car")));
            GraphHopper h = new HarumiGraphHopper();
            h.init(cfg);
            if (!h.load()) throw new IOException("Offline graph could not be loaded");
            hopper = h;
            Log.i(TAG, "grafo offline carregado em " + (System.nanoTime() - t0) / 1000000 + " ms");
            return h;
        } catch (IOException e) {
            failed = true; Log.e(TAG, "grafo offline: " + e); throw e;
        } catch (Throwable e) { // inclui NoClassDefFoundError/OutOfMemoryError: nao derruba o app
            failed = true; Log.e(TAG, "grafo offline falhou", e); throw new IOException("Offline router failed: " + e);
        }
    }

    /** Rota local em JSON no formato OSRM (code, routes[0]). IOException se indisponivel ou sem rota. O rumo e ignorado (CH nao suporta). */
    public String routeJson(double fromLat, double fromLon, double toLat, double toLon, Double bearing) throws IOException {
        long t0 = System.nanoTime();
        GraphHopper h = load();
        GHRequest req = new GHRequest(fromLat, fromLon, toLat, toLon).setProfile("car").setLocale(new Locale("pt", "BR"));
        GHResponse rsp;
        try { rsp = h.route(req); } catch (RuntimeException | OutOfMemoryError e) { Log.e(TAG, "rota offline falhou", e); throw new IOException("Offline route failed: " + e); }
        if (rsp.hasErrors()) throw new IOException("No offline route: " + rsp.getErrors().get(0).getMessage());
        ResponsePath p = rsp.getBest();
        String json = toOsrmJson(p.getPoints(), p.getDistance(), p.getTime() / 1000.0, p.getInstructions());
        Log.i(TAG, String.format(Locale.ROOT, "rota offline=true calculo=%d ms dist=%.1f km tempo=%d min pontos=%d",
                (System.nanoTime() - t0) / 1000000, p.getDistance() / 1000, Math.round(p.getTime() / 60000.0), p.getPoints().size()));
        return json;
    }

    /** Tipo e modificador OSRM para um sinal do GraphHopper: {type, modifier} (modifier pode ser null). Funcao pura. */
    static String[] maneuverFor(int sign) {
        switch (sign) {
            case Instruction.TURN_LEFT: return new String[]{"turn", "left"};
            case Instruction.TURN_SHARP_LEFT: return new String[]{"turn", "sharp left"};
            case Instruction.TURN_SLIGHT_LEFT: return new String[]{"turn", "slight left"};
            case Instruction.TURN_RIGHT: return new String[]{"turn", "right"};
            case Instruction.TURN_SHARP_RIGHT: return new String[]{"turn", "sharp right"};
            case Instruction.TURN_SLIGHT_RIGHT: return new String[]{"turn", "slight right"};
            case Instruction.CONTINUE_ON_STREET: return new String[]{"continue", "straight"};
            case Instruction.U_TURN_LEFT: case Instruction.U_TURN_RIGHT: case Instruction.U_TURN_UNKNOWN: return new String[]{"turn", "uturn"};
            case Instruction.KEEP_LEFT: return new String[]{"fork", "slight left"};
            case Instruction.KEEP_RIGHT: return new String[]{"fork", "slight right"};
            case Instruction.USE_ROUNDABOUT: return new String[]{"roundabout", "right"};
            case Instruction.LEAVE_ROUNDABOUT: return new String[]{"exit roundabout", "right"};
            case Instruction.FINISH: return new String[]{"arrive", null};
            default: return new String[]{"notification", null}; // REACHED_VIA, FERRY, UNKNOWN, IGNORE...
        }
    }

    private static String toOsrmJson(PointList pts, double distance, double durationS, InstructionList ins) {
        StringBuilder b = new StringBuilder(pts.size() * 24 + 2048);
        b.append("{\"code\":\"Ok\",\"source\":\"offline\",\"routes\":[{\"geometry\":{\"type\":\"LineString\",\"coordinates\":[");
        for (int i = 0; i < pts.size(); i++) {
            if (i > 0) b.append(',');
            b.append('[').append(coord(pts.getLon(i))).append(',').append(coord(pts.getLat(i))).append(']');
        }
        b.append("]},\"distance\":").append(coord(distance)).append(",\"duration\":").append(coord(durationS)).append(",\"legs\":[{\"steps\":[");
        for (int i = 0; i < ins.size(); i++) {
            Instruction in = ins.get(i);
            String[] m = maneuverFor(in.getSign());
            if (i == 0 && in.getSign() == Instruction.CONTINUE_ON_STREET) m = new String[]{"depart", "straight"};
            PointList ip = in.getPoints();
            double lon = ip.size() > 0 ? ip.getLon(0) : pts.getLon(pts.size() - 1), lat = ip.size() > 0 ? ip.getLat(0) : pts.getLat(pts.size() - 1);
            if (i > 0) b.append(',');
            b.append("{\"name\":\"").append(esc(in.getName())).append("\",\"distance\":").append(coord(in.getDistance()))
             .append(",\"duration\":").append(coord(in.getTime() / 1000.0)).append(",\"maneuver\":{\"type\":\"").append(m[0]).append('"');
            if (m[1] != null) b.append(",\"modifier\":\"").append(m[1]).append('"');
            if (in instanceof RoundaboutInstruction) { int ex = ((RoundaboutInstruction) in).getExitNumber(); if (ex >= 1) b.append(",\"exit\":").append(ex); }
            b.append(",\"location\":[").append(coord(lon)).append(',').append(coord(lat)).append("]}}");
        }
        return b.append("]}]}]}").toString();
    }

    private static String coord(double d) {
        if (!Double.isFinite(d)) return "0";
        return new java.math.BigDecimal(d).setScale(6, java.math.RoundingMode.HALF_UP).stripTrailingZeros().toPlainString();
    }

    private static String esc(String s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 0x20) b.append(String.format(Locale.ROOT, "\\u%04x", (int) c));
            else b.append(c);
        }
        return b.toString();
    }
}
