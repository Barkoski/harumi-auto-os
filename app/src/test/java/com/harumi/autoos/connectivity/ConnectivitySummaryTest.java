package com.harumi.autoos.connectivity;
import org.junit.Test;
import static org.junit.Assert.*;
public class ConnectivitySummaryTest {
    @Test public void offlineDoesNotClaimInternet() { assertEquals("Sem conexão de rede",ConnectivitySummary.describe(false,false,false,false,"")); }
    @Test public void connectedIsNotEnough() { assertTrue(ConnectivitySummary.describe(true,true,false,false,"Wi-Fi").contains("não confirmada")); }
    @Test public void validatedConnectionReportsTransport() { assertEquals("Internet disponível · Bluetooth",ConnectivitySummary.describe(true,true,true,false,"Bluetooth")); }
    @Test public void captivePortalRequiresSignIn() { assertTrue(ConnectivitySummary.describe(true,true,false,true,"Wi-Fi").contains("entre na rede")); }
    @Test public void cableWithoutInternetIsNotOnline() { assertFalse(ConnectivitySummary.describe(true,false,false,false,"Ethernet / cabo").startsWith("Internet disponível")); }
}
