package com.harumi.autoos.navigation;
import org.junit.Test;
import static org.junit.Assert.*;
public class RouteCoordinatesTest {
    @Test public void keepsLongitudeLatitudeOrder(){assertEquals("-54.635560,-16.470830;-51.162780,-23.310280",RouteCoordinates.toProviderPath("-54.63556,-16.47083,-51.16278,-23.31028"));}
    @Test public void rejectsUrlsMissingPointsAndOutsideBounds(){for(String s:new String[]{"https://evil.example","1,2","NaN,-10,-50,-20","-54,-16,-51,90","-540,-16,-51,-20","-54,-16,-51,-20,0"}){try{RouteCoordinates.toProviderPath(s);fail(s);}catch(IllegalArgumentException expected){}}}
}
