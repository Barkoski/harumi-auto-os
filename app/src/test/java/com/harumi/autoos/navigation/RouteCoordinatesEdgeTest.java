package com.harumi.autoos.navigation;
import org.junit.Test;
import static org.junit.Assert.*;
/** Casos de borda de RouteCoordinates: limite de 100 caracteres, regex [-0-9.,]+, 4 valores, longitude -75..-30, latitude -35..6. */
public class RouteCoordinatesEdgeTest {
    private static void assertRejected(String s){
        try{RouteCoordinates.toProviderPath(s);fail("Deveria rejeitar: "+s);}catch(IllegalArgumentException expected){}
    }
    private static String zeros(int n){StringBuilder b=new StringBuilder();for(int i=0;i<n;i++)b.append('0');return b.toString();}

    @Test public void rejectsNull(){assertRejected(null);}
    @Test public void rejectsEmptyString(){assertRejected("");}
    @Test public void rejectsScientificNotation(){assertRejected("1e5");assertRejected("-5e1,-10,-40,-20");}
    @Test public void rejectsLoneMinusAndDot(){assertRejected("-.");assertRejected("-.,-.,-.,-.");assertRejected(".,.,.,.");}
    @Test public void rejectsOnlyCommas(){assertRejected(",,,");assertRejected(",,,,");assertRejected(",");}
    @Test public void rejectsWhitespaceAndPlusSign(){assertRejected(" -50,-10,-40,-20");assertRejected("+50,-10,-40,-20");assertRejected("-50,-10,-40,-20\n");}
    @Test public void rejectsMalformedNumbers(){assertRejected("--50,-10,-40,-20");assertRejected("-5.0.0,-10,-40,-20");assertRejected("-50,-10,-40,");}

    @Test public void acceptsExactly100Characters(){
        String s="-50."+zeros(84)+",-10,-40,-20";
        assertEquals(100,s.length());
        assertEquals("-50.000000,-10.000000;-40.000000,-20.000000",RouteCoordinates.toProviderPath(s));
    }
    @Test public void rejects101CharactersEvenIfValid(){
        String s="-50."+zeros(85)+",-10,-40,-20";
        assertEquals(101,s.length());
        assertRejected(s);
    }

    @Test public void acceptsLongitudeBoundsInBothPoints(){
        assertEquals("-75.000000,-10.000000;-30.000000,-20.000000",RouteCoordinates.toProviderPath("-75,-10,-30,-20"));
        assertEquals("-30.000000,-10.000000;-75.000000,-20.000000",RouteCoordinates.toProviderPath("-30,-10,-75,-20"));
    }
    @Test public void acceptsLatitudeBoundsInBothPoints(){
        assertEquals("-50.000000,-35.000000;-40.000000,6.000000",RouteCoordinates.toProviderPath("-50,-35,-40,6"));
        assertEquals("-50.000000,6.000000;-40.000000,-35.000000",RouteCoordinates.toProviderPath("-50,6,-40,-35"));
    }
    @Test public void rejectsLongitudeJustOutside(){
        assertRejected("-75.000001,-10,-40,-20");
        assertRejected("-29.999999,-10,-40,-20");
        assertRejected("-50,-10,-75.000001,-20");
        assertRejected("-50,-10,-29.999999,-20");
    }
    @Test public void rejectsLatitudeJustOutside(){
        assertRejected("-50,-35.000001,-40,-20");
        assertRejected("-50,6.000001,-40,-20");
        assertRejected("-50,-10,-40,-35.000001");
        assertRejected("-50,-10,-40,6.000001");
    }
    @Test public void acceptsJustInsideBounds(){
        assertEquals("-74.999999,-34.999999;-30.000001,5.999999",RouteCoordinates.toProviderPath("-74.999999,-34.999999,-30.000001,5.999999"));
    }
    @Test public void rejectsPositiveLongitudeAndSwappedOrder(){
        assertRejected("50,-10,-40,-20");
        assertRejected("-10,-50,-20,-40"); // latitude/longitude trocadas: lon -10 fora de -75..-30
    }
    @Test public void rejectsWrongNumberOfValues(){
        assertRejected("-50,-10,-40");
        assertRejected("-50,-10,-40,-20,-30,-10");
    }
}
