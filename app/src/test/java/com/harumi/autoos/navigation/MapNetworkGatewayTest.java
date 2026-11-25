package com.harumi.autoos.navigation;
import static org.junit.Assert.*;
import org.junit.Test;

public class MapNetworkGatewayTest {
    @Test public void userAgentContainsPassedVersion() {
        String ua = MapNetworkGateway.userAgent("9.8.7-test");
        assertTrue(ua, ua.startsWith("HarumiAutoOS/9.8.7-test "));
        assertTrue(ua.contains("com.harumi.autoos"));
    }
    @Test public void userAgentFallsBackWhenVersionMissing() {
        assertTrue(MapNetworkGateway.userAgent(null).startsWith("HarumiAutoOS/unknown "));
        assertTrue(MapNetworkGateway.userAgent(" ").startsWith("HarumiAutoOS/unknown "));
    }
    private static final String PTS = "-51.16278,-23.31028,-51.15,-23.3";
    private static void assertBadQuery(String q) {
        try { MapNetworkGateway.validateQuery(q); fail("Deveria rejeitar: " + q); } catch (IllegalArgumentException expected) { }
    }
    @Test public void validateQueryRejectsEmptyLongUrlAndControl() {
        assertBadQuery(null); assertBadQuery(""); assertBadQuery("   ");
        assertBadQuery(new String(new char[121]).replace('\0', 'a'));
        assertBadQuery("https://evil.example"); assertBadQuery("foo HTTP bar");
        assertBadQuery("rua\nx"); assertBadQuery("rua\u0000x");
    }
    @Test public void validateQueryAcceptsNormalAndLimit() {
        assertEquals("Rua Sergipe, Londrina", MapNetworkGateway.validateQuery("  Rua Sergipe, Londrina "));
        assertEquals(120, MapNetworkGateway.validateQuery(new String(new char[120]).replace('\0', 'a')).length());
    }
    @Test public void bearingParsing() {
        assertNull(RouteCoordinates.parseBearing("-1"));
        assertEquals(Integer.valueOf(0), RouteCoordinates.parseBearing("0"));
        assertEquals(Integer.valueOf(359), RouteCoordinates.parseBearing("359"));
        assertNull(RouteCoordinates.parseBearing("360"));
        assertNull(RouteCoordinates.parseBearing("abc"));
        assertNull(RouteCoordinates.parseBearing(null));
    }
    @Test public void routeUrlWithAndWithoutBearing() {
        String base = "https://router.project-osrm.org/route/v1/driving/-51.162780,-23.310280;-51.150000,-23.300000?steps=true&overview=full&geometries=geojson&alternatives=false";
        assertEquals(base, MapNetworkGateway.routeUrl(PTS, null));
        assertEquals(base + "&bearings=90,45;", MapNetworkGateway.routeUrl(PTS, 90));
    }
    @Test public void geocodeUrlWithoutViewbox() {
        String u = MapNetworkGateway.geocodeUrl("Rua Sergipe", null, null);
        assertEquals("https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=br&limit=5&q=Rua+Sergipe", u);
        assertFalse(MapNetworkGateway.geocodeUrl("x", "-23.3", null).contains("viewbox"));
        assertFalse(MapNetworkGateway.geocodeUrl("x", "abc", "-51.1").contains("viewbox"));
        assertFalse(MapNetworkGateway.geocodeUrl("x", "95", "-51.1").contains("viewbox"));
    }
    @Test public void geocodeUrlWithViewbox() {
        String u = MapNetworkGateway.geocodeUrl("Londrina", "-23.3", "-51.1");
        assertTrue(u, u.endsWith("&q=Londrina&viewbox=-51.6000,-22.8000,-50.6000,-23.8000&bounded=0"));
    }
    @Test public void normalizesNominatimSample() throws Exception {
        String json = "[{\"place_id\":1,\"lat\":\"-23.3103\",\"lon\":\"-51.1628\",\"display_name\":\"Londrina, Paran\\u00e1, Brasil \\\"x\\\"\",\"boundingbox\":[\"1\",\"2\"]},"
            + "{\"lat\":\"abc\",\"lon\":\"1\",\"display_name\":\"ruim\"},"
            + "{\"lat\":\"-23.0\",\"lon\":\"-51.0\",\"display_name\":\"" + new String(new char[200]).replace('\0', 'b') + "\"}]";
        String out = MapNetworkGateway.normalizeGeocode(json);
        assertTrue(out, out.startsWith("[{\"name\":\"Londrina, Paraná, Brasil \\\"x\\\"\",\"lat\":-23.3103,\"lon\":-51.1628},{\"name\":\"bbbb"));
        assertTrue(out, out.endsWith("\",\"lat\":-23,\"lon\":-51}]"));
        assertFalse(out.contains("ruim"));
        assertEquals("[]", MapNetworkGateway.normalizeGeocode("[]"));
    }
    @Test public void normalizeRejectsNonArray() {
        try { MapNetworkGateway.normalizeGeocode("{\"error\":1}"); fail(); } catch (java.io.IOException expected) { }
        try { MapNetworkGateway.normalizeGeocode("not json"); fail(); } catch (java.io.IOException expected) { }
    }
    private static final String TPL = "https://tiles.openfreemap.org/planet/20261101_080013_pt/{z}/{x}/{y}.pbf";
    @Test public void tileTemplateFromTileJson() throws Exception {
        assertEquals(TPL, MapNetworkGateway.parseTileTemplate("{\"tilejson\":\"3.0.0\",\"tiles\":[\"" + TPL + "\"],\"maxzoom\":14}"));
    }
    @Test public void tileTemplateRejectsOtherHostsAndShapes() {
        String[] bad = {"{\"tiles\":[\"https://evil.example/planet/{z}/{x}/{y}.pbf\"]}",
            "{\"tiles\":[\"http://tiles.openfreemap.org/planet/{z}/{x}/{y}.pbf\"]}",
            "{\"tiles\":[\"https://tiles.openfreemap.org.evil.example/p/{z}/{x}/{y}.pbf\"]}",
            "{\"tiles\":[\"https://tiles.openfreemap.org/../x/{z}/{x}/{y}.pbf\"]}",
            "{\"tiles\":[\"https://tiles.openfreemap.org/planet/{z}/{x}/{y}.pbf?k=1\"]}",
            "{\"tiles\":[]}", "{\"x\":1}", "[]", "nao e json"};
        for (String b : bad) { try { MapNetworkGateway.parseTileTemplate(b); fail("Deveria rejeitar: " + b); } catch (java.io.IOException expected) { } }
    }
    @Test public void vectorTileUrlBuildsAndValidates() {
        assertEquals("https://tiles.openfreemap.org/planet/20261101_080013_pt/14/6021/9267.pbf", MapNetworkGateway.vectorTileUrl(TPL, 14, 6021, 9267));
        assertEquals("https://tiles.openfreemap.org/planet/20261101_080013_pt/0/0/0.pbf", MapNetworkGateway.vectorTileUrl(TPL, 0, 0, 0));
        int[][] bad = {{15, 0, 0}, {-1, 0, 0}, {3, 8, 0}, {3, 0, 8}, {3, -1, 0}, {0, 1, 0}};
        for (int[] b : bad) { try { MapNetworkGateway.vectorTileUrl(TPL, b[0], b[1], b[2]); fail("Deveria rejeitar"); } catch (IllegalArgumentException expected) { } }
    }
    @Test public void glyphsUrlValidatesFontstackAndRange() {
        assertEquals("https://tiles.openfreemap.org/fonts/Noto%20Sans%20Regular/0-255.pbf", MapNetworkGateway.glyphsUrl("Noto Sans Regular", "0-255"));
        assertEquals("https://tiles.openfreemap.org/fonts/Noto%20Sans%20Bold%2CNoto%20Sans%20Regular/256-511.pbf", MapNetworkGateway.glyphsUrl("Noto Sans Bold,Noto Sans Regular", "256-511"));
        String[][] bad = {{"../x", "0-255"}, {"a/b", "0-255"}, {"Noto Sans?x", "0-255"}, {"", "0-255"}, {null, "0-255"}, {"Noto Sans", "0-255.pbf"}, {"Noto Sans", "abc"}, {"Noto Sans", null}, {"Noto Sans", "0-255/../x"}, {"Noto1", "0-255"}};
        for (String[] b : bad) { try { MapNetworkGateway.glyphsUrl(b[0], b[1]); fail("Deveria rejeitar: " + b[0] + " " + b[1]); } catch (IllegalArgumentException expected) { } }
    }
    @Test public void gunzipOnlyWhenGzipMagic() throws Exception {
        byte[] raw = {0x1a, (byte) 0xd7, 0x01, 0x0a, 0x04, 0x70, 0x61, 0x72, 0x6b};
        assertSame(raw, MapNetworkGateway.gunzipIfNeeded(raw, 100));
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gz = new java.util.zip.GZIPOutputStream(bos)) { gz.write(raw); }
        assertArrayEquals(raw, MapNetworkGateway.gunzipIfNeeded(bos.toByteArray(), 100));
        assertEquals(0, MapNetworkGateway.gunzipIfNeeded(new byte[0], 100).length);
    }
    @Test public void gunzipRespectsLimit() throws Exception {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
        try (java.util.zip.GZIPOutputStream gz = new java.util.zip.GZIPOutputStream(bos)) { gz.write(new byte[50000]); }
        try { MapNetworkGateway.gunzipIfNeeded(bos.toByteArray(), 1000); fail(); } catch (java.io.IOException expected) { }
    }
}
