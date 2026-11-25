package com.harumi.autoos.ai.tools;
import java.util.Map;
public record ToolCall(String toolId,Map<String,String> slots,Origin origin,String requestId) {
    public ToolCall { slots=slots==null?Map.of():Map.copyOf(slots); }
}
