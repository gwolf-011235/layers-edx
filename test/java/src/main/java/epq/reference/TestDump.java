package epq.reference;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Unified CLI entry point for all Java reference dumps.
 *
 * Supports:
 *
 * Single mode:
 * java epq.reference.TestDump XRayTransition Z=1 trans=1
 *
 * Batch mode (stdin-driven):
 * java epq.reference.TestDump batch
 *
 * stdin:
 * XRayTransition Z=1 trans=1
 * Element Z=79
 *
 * Java acts purely as a reference oracle and emits deterministic CSV.
 */
public final class TestDump {

    private static final Map<String, DumpModule> MODULES = Stream.of(
            new DumpXRayTransition(),
            new DumpElement(),
            new DumpAtomicShell(),
            new DumpCompositionDetail(),
            new DumpCompositionSummary()
    // add more here
    ).collect(Collectors.toMap(DumpModule::name, m -> m));

    private static DumpModule lookup(String name) {
        return MODULES.get(name);
    }

    private enum Framing {
        NONE,
        BATCH
    }

    public static void main(String[] args) {
        try {
            if (args.length > 0 && args[0].equals("batch")) {
                runBatch();
            } else {
                runSingle(args);
            }
        } catch (Exception e) {
            System.err
                    .println("Exception caught in TestDump (" + e.getClass().getSimpleName() + "): " + e.getMessage());
            e.printStackTrace(System.err);
            System.exit(1);
        }
    }

    private static void runSingle(String[] args) {
        if (args.length == 0) {
            usageAndExit("No dump module specified", null);
        }

        String command = args[0];
        String[] cmdArgs = Arrays.copyOfRange(args, 1, args.length);

        runCommand(command, cmdArgs, Framing.NONE);
    }

    private static void runBatch() throws Exception {
        BufferedReader in = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));

        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            runOneBatchLine(line);
        }
    }

    private static void runOneBatchLine(String line) {
        String[] tokens = line.split("\\s+");
        String command = tokens[0];
        String[] cmdArgs = Arrays.copyOfRange(tokens, 1, tokens.length);

        runCommand(command, cmdArgs, Framing.BATCH);
    }

    private static void runCommand(
            String command,
            String[] cmdArgs,
            Framing framing) {

        DumpModule module = lookup(command);
        if (module == null) {
            usageAndExit("Unknown dump module: " + command, null);
        }

        try {
            DumpContext ctx = new DumpContext(module.schema(), cmdArgs);

            if (framing == Framing.BATCH) {
                emitBegin(module.name(), ctx);
            }

            module.run(ctx);
            ctx.flush();

            if (framing == Framing.BATCH) {
                emitEnd();
            }
        } catch (IllegalArgumentException e) {
            usageAndExit(e.getMessage(), module);
        }
    }

    private static void emitBegin(String module, DumpContext ctx) {
        System.out.print("#BEGIN dump=");
        System.out.print(module);

        for (Map.Entry<String, String> e : ctx.args().entrySet()) {
            System.out.print(" ");
            System.out.print(e.getKey());
            System.out.print("=");
            System.out.print(e.getValue());
        }

        System.out.println();
    }

    private static void emitEnd() {
        System.out.println("#END");
        System.out.println();
    }

    private static void usageAndExit(String error, DumpModule module) {
        if (error != null && !error.isEmpty()) {
            System.err.println("Error: " + error);
            System.err.println();
        }

        if (module != null && !module.usage().isEmpty()) {
            System.err.println("Module usage:");
            System.err.println("  " + module.usage());
        } else {
            usage();
        }

        System.exit(1);
    }

    private static void usage() {
        System.err.println("Usage:");
        System.err.println("  TestDump <command> [key=value ...]");
        System.err.println("  TestDump batch   (reads stdin)");
        System.err.println();
        System.err.println("Available dumps:");
        for (String name : MODULES.keySet()) {
            System.err.println("  " + name);
        }
    }

}
