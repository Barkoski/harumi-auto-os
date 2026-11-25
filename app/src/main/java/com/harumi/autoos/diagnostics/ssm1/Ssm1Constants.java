package com.harumi.autoos.diagnostics.ssm1;
import java.util.List;
/*
 * NÃO VERIFICADO – valores de memória; confirmar com documentação e no carro antes de uso real.
 * Subaru Impreza SW 1993 (pré-OBD-II), Subaru Select Monitor (SSM1). Somente comandos de LEITURA.
 */
public final class Ssm1Constants {
    private Ssm1Constants() { }
    public static final int BAUD = 1953;
    public static final char PARITY = 'E';
    public static final int DATA_BITS = 8;
    public static final int STOP_BITS = 1;
    /** Leitura de endereço: READ_OPCODE addrHi addrLo 0x00. */
    public static final int READ_OPCODE = 0x78;
    /** Parada de leitura contínua. */
    public static final byte[] STOP_COMMAND = {0x12, 0x00, 0x00, 0x00};
    public static final int UNCONFIRMED_ADDRESS = -1;
    /** Parâmetro candidato; fórmula valor = bruto * scale + offset é HIPÓTESE. */
    public record Param(String key, String label, String unit, int address, double scale, double offset) {
        public boolean confirmed() { return address >= 0; }
    }
    /** Endereços "a confirmar"; fórmulas são hipóteses (a confirmar no carro). */
    public static final List<Param> CANDIDATES = List.of(
        new Param("rpm", "rotação do motor", "rpm", UNCONFIRMED_ADDRESS, 25.0, 0),
        new Param("coolant_temp", "temperatura do líquido de arrefecimento", "°C", UNCONFIRMED_ADDRESS, 1.0, -50),
        new Param("battery_voltage", "tensão da bateria", "V", UNCONFIRMED_ADDRESS, 0.08, 0),
        new Param("speed", "velocidade", "km/h", UNCONFIRMED_ADDRESS, 1.0, 0));
}
