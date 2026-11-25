package com.harumi.autoos.navigation;
import static org.junit.Assert.*;
import com.graphhopper.util.Instruction;
import org.junit.Test;

public class OfflineRouterTest {
    private static void check(int sign, String type, String modifier) {
        String[] m = OfflineRouter.maneuverFor(sign);
        assertEquals("type " + sign, type, m[0]);
        assertEquals("modifier " + sign, modifier, m[1]);
    }
    @Test public void turns() {
        check(Instruction.TURN_LEFT, "turn", "left");
        check(Instruction.TURN_SHARP_LEFT, "turn", "sharp left");
        check(Instruction.TURN_SLIGHT_LEFT, "turn", "slight left");
        check(Instruction.TURN_RIGHT, "turn", "right");
        check(Instruction.TURN_SHARP_RIGHT, "turn", "sharp right");
        check(Instruction.TURN_SLIGHT_RIGHT, "turn", "slight right");
    }
    @Test public void continueUturnsForksAndEnd() {
        check(Instruction.CONTINUE_ON_STREET, "continue", "straight");
        check(Instruction.U_TURN_LEFT, "turn", "uturn");
        check(Instruction.U_TURN_RIGHT, "turn", "uturn");
        check(Instruction.U_TURN_UNKNOWN, "turn", "uturn");
        check(Instruction.KEEP_LEFT, "fork", "slight left");
        check(Instruction.KEEP_RIGHT, "fork", "slight right");
        check(Instruction.FINISH, "arrive", null);
    }
    @Test public void roundaboutAndUnknown() {
        check(Instruction.USE_ROUNDABOUT, "roundabout", "right");
        check(Instruction.LEAVE_ROUNDABOUT, "exit roundabout", "right");
        check(Instruction.REACHED_VIA, "notification", null);
        check(Instruction.FERRY, "notification", null);
        check(Instruction.UNKNOWN, "notification", null);
        check(Instruction.IGNORE, "notification", null);
    }
}
