import com.graphhopper.GraphHopperConfig;
import com.graphhopper.config.CHProfile;
import com.graphhopper.config.Profile;
import com.harumi.autoos.navigation.gh.HarumiGraphHopper;
import java.util.List;

/** Import do grafo do Brasil com o peso de carro proprio (sem Janino). Uso: HarumiImport arquivo.osm.pbf pasta-do-grafo */
public final class HarumiImport {
    public static void main(String[] a) {
        GraphHopperConfig cfg = new GraphHopperConfig();
        cfg.putObject("datareader.file", a[0]);
        cfg.putObject("graph.location", a[1]);
        cfg.putObject("graph.dataaccess.default_type", "MMAP_STORE");
        cfg.putObject("graph.encoded_values", "car_access, car_average_speed, road_access");
        cfg.putObject("import.osm.ignored_highways", "footway,construction,cycleway,path,steps");
        cfg.putObject("prepare.min_network_size", 200);
        cfg.putObject("prepare.subnetworks.threads", 1);
        cfg.putObject("routing.snap_preventions_default", "tunnel, bridge, ferry");
        cfg.setProfiles(List.of(HarumiGraphHopper.carProfile()));
        cfg.setCHProfiles(List.of(new CHProfile("car")));
        HarumiGraphHopper h = new HarumiGraphHopper();
        h.init(cfg);
        h.importOrLoad();
        h.close();
    }
}
