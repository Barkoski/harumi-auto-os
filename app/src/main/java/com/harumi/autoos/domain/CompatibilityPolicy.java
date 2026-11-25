package com.harumi.autoos.domain;
import java.util.List;
public final class CompatibilityPolicy {
    private CompatibilityPolicy() { }
    public static String evaluate(int api, List<String> abis, boolean process64) {
        if(api<26) return "BLOQUEADO: exige Android 8 / API 26+.";
        if(!abis.contains("arm64-v8a")&&!abis.contains("x86_64")) return "BLOQUEADO: APK com IA apenas ARM64/x86_64; Android somente 32 bits não é compatível.";
        if(!process64) return "BLOQUEADO: processo de 32 bits; esta IA exige 64 bits.";
        if(!abis.contains("arm64-v8a")) return "BANCADA x86_64: não comprova compatibilidade com a central ARM.";
        return "PRÉ-REQUISITOS BÁSICOS ATENDIDOS: ARM64 / Android 8+. Desempenho, áudio, ré/360° e ACC exigem teste físico.";
    }
}
