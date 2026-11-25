package com.harumi.autoos.navigation;
import static org.junit.Assert.*;
import java.io.File;
import java.util.Arrays;
import java.util.List;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

public class OfflineTilesTest {
    // Bounds de exemplo para o Brasil: oeste,sul,leste,norte
    private static final double[] BR = OfflineTiles.parseBounds("-74.0,-34.0,-28.0,5.5");
    @Rule public TemporaryFolder tmp = new TemporaryFolder();

    @Test public void tmsRowInvertsY() {
        assertEquals(0, OfflineTiles.tmsRow(0, 0));
        assertEquals(1, OfflineTiles.tmsRow(1, 0));
        assertEquals(0, OfflineTiles.tmsRow(1, 1));
        assertEquals(4, OfflineTiles.tmsRow(3, 3));
        assertEquals((1 << 14) - 1, OfflineTiles.tmsRow(14, 0));
        assertEquals(0, OfflineTiles.tmsRow(14, (1 << 14) - 1));
    }
    @Test public void candidatePathsOrderAndNulls() {
        File ext = new File("ext/mapas"), in = new File("int/mapas");
        List<File> c = OfflineTiles.candidatePaths(ext, in);
        assertEquals(Arrays.asList(new File(ext, "brasil.mbtiles"), new File(in, "brasil.mbtiles")), c);
        assertEquals(1, OfflineTiles.candidatePaths(null, in).size());
        assertEquals(new File(in, "brasil.mbtiles"), OfflineTiles.candidatePaths(null, in).get(0));
        assertTrue(OfflineTiles.candidatePaths(null, null).isEmpty());
    }
    @Test public void firstExistingPrefersExternalAndIgnoresEmptyOrMissing() throws Exception {
        File ext = tmp.newFolder("ext"), in = tmp.newFolder("in");
        List<File> c = OfflineTiles.candidatePaths(ext, in);
        assertNull(OfflineTiles.firstExisting(c));                 // sem arquivo: volta para online
        File fi = new File(in, "brasil.mbtiles");
        java.nio.file.Files.write(fi.toPath(), new byte[]{1});
        assertEquals(fi, OfflineTiles.firstExisting(c));           // so o interno
        File fe = new File(ext, "brasil.mbtiles");
        assertTrue(fe.createNewFile());                            // vazio: ignorado
        assertEquals(fi, OfflineTiles.firstExisting(c));
        java.nio.file.Files.write(fe.toPath(), new byte[]{1});
        assertEquals(fe, OfflineTiles.firstExisting(c));           // externo ganha
        assertNull(OfflineTiles.firstExisting(OfflineTiles.candidatePaths(null, null)));
    }
    @Test public void parseBounds() {
        assertArrayEquals(new double[]{-74, -34, -28, 5.5}, BR, 1e-9);
        assertNull(OfflineTiles.parseBounds(null));
        assertNull(OfflineTiles.parseBounds(""));
        assertNull(OfflineTiles.parseBounds("1,2,3"));
        assertNull(OfflineTiles.parseBounds("a,b,c,d"));
        assertNull(OfflineTiles.parseBounds("10,0,5,1"));      // oeste >= leste
        assertNull(OfflineTiles.parseBounds("0,0,1,95"));      // latitude invalida
        assertNotNull(OfflineTiles.parseBounds(" -74.0 , -34 , -28 , 5.5 "));
    }
    @Test public void insideBoundsRule() {
        // Londrina (-51.16, -23.31) em z8 => x=91, y=145 (calculo abaixo confere)
        int x = (int) Math.floor((-51.16 + 180) / 360 * 256);
        double lat = Math.toRadians(-23.31);
        int y = (int) Math.floor((1 - Math.log(Math.tan(lat) + 1 / Math.cos(lat)) / Math.PI) / 2 * 256);
        assertEquals(91, x); assertEquals(145, y);
        assertTrue(OfflineTiles.insideBounds(8, x, y, BR));
        assertTrue(OfflineTiles.insideBounds(14, 6000, 9000, new double[]{-180, -85, 180, 85}));
        assertFalse(OfflineTiles.insideBounds(8, 86, 154, BR));   // Buenos Aires, ao sul de -34
        assertFalse(OfflineTiles.insideBounds(8, 128, 90, BR));   // hemisferio norte / Europa
        assertFalse(OfflineTiles.insideBounds(0, 0, 0, BR));      // tile mundial nunca esta inteiro dentro
        assertFalse(OfflineTiles.insideBounds(6, 22, 39, BR));    // borda sul (-34): parcialmente fora => Internet
    }
    @Test public void insideBoundsRejectsBadInput() {
        assertFalse(OfflineTiles.insideBounds(8, 89, 144, null));
        assertFalse(OfflineTiles.insideBounds(8, 89, 144, new double[]{1, 2, 3}));
        assertFalse(OfflineTiles.insideBounds(8, -1, 144, BR));
        assertFalse(OfflineTiles.insideBounds(8, 256, 144, BR));
        assertFalse(OfflineTiles.insideBounds(8, 89, 256, BR));
        assertFalse(OfflineTiles.insideBounds(-1, 0, 0, BR));
    }
    @Test public void tileGeometry() {
        assertEquals(-180.0, OfflineTiles.tileWest(3, 0), 1e-9);
        assertEquals(180.0, OfflineTiles.tileWest(3, 8), 1e-9);
        assertEquals(85.0511, OfflineTiles.tileNorth(3, 0), 1e-3);
        assertEquals(0.0, OfflineTiles.tileNorth(1, 1), 1e-9);
    }
}
