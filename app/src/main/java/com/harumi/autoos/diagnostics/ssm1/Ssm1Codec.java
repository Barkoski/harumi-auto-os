package com.harumi.autoos.diagnostics.ssm1;
/** Monta apenas requisições de leitura/parada e decodifica respostas (eco do endereço + 1 byte de dado). NÃO VERIFICADO. */
public final class Ssm1Codec {
    public static final int RESPONSE_LENGTH = 3;
    private Ssm1Codec() { }
    public static byte[] readRequest(int address) {
        checkAddress(address);
        return new byte[]{(byte) Ssm1Constants.READ_OPCODE, (byte) (address >> 8), (byte) address, 0x00};
    }
    public static byte[] stopRequest() { return Ssm1Constants.STOP_COMMAND.clone(); }
    /** Retorna o byte de dado (0..255); lança IllegalArgumentException se tamanho ou eco forem inválidos. */
    public static int decodeResponse(int address, byte[] response) {
        checkAddress(address);
        if (response == null || response.length != RESPONSE_LENGTH) throw new IllegalArgumentException("Resposta com tamanho inválido");
        if ((response[0] & 0xFF) != (address >> 8) || (response[1] & 0xFF) != (address & 0xFF)) throw new IllegalArgumentException("Eco de endereço divergente");
        return response[2] & 0xFF;
    }
    private static void checkAddress(int a) { if (a < 0 || a > 0xFFFF) throw new IllegalArgumentException("Endereço fora de 0..0xFFFF: " + a); }
}
