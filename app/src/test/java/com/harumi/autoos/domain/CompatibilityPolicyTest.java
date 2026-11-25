package com.harumi.autoos.domain;
import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;
public class CompatibilityPolicyTest {
    @Test public void rejectsOldAndroid(){assertTrue(CompatibilityPolicy.evaluate(25,List.of("arm64-v8a"),true).startsWith("BLOQUEADO"));}
    @Test public void rejects32bitOs(){assertTrue(CompatibilityPolicy.evaluate(30,List.of("armeabi-v7a"),false).contains("somente 32 bits"));}
    @Test public void rejects32bitProcess(){assertTrue(CompatibilityPolicy.evaluate(30,List.of("arm64-v8a"),false).contains("processo de 32"));}
    @Test public void distinguishesBench(){assertTrue(CompatibilityPolicy.evaluate(30,List.of("x86_64"),true).startsWith("BANCADA"));}
    @Test public void doesNotHomologateSpecs(){assertTrue(CompatibilityPolicy.evaluate(30,List.of("arm64-v8a"),true).contains("teste físico"));}
}
