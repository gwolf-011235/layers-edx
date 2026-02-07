package epq.reference;

import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Execution context for a single dump invocation.
 *
 * Responsibilities:
 * - Parse key=value arguments
 * - Provide deterministic argument access
 * - Emit CSV output with auto-header support
 *
 * Does NOT:
 * - Know about dump modules
 * - Validate business logic
 * - Handle CLI errors or usage
 */
public final class DumpContext {

    private final LinkedHashMap<String, String> args;
    private final PrintWriter out;
    private final CsvWriter csv;

    public DumpContext(CsvSchema schema, String[] argv) throws IllegalArgumentException {
        this.args = parseArgs(argv);
        this.out = new PrintWriter(new OutputStreamWriter(System.out, StandardCharsets.UTF_8),
                false);
        this.csv = new CsvWriter(out, schema);
    }

    /**
     * Parse key=value arguments into a map.
     *
     * @throws IllegalArgumentException on parse errors
     */
    private static LinkedHashMap<String, String> parseArgs(String[] argv) throws IllegalArgumentException {
        LinkedHashMap<String, String> map = new LinkedHashMap<>();

        for (String arg : argv) {
            int idx = arg.indexOf('=');
            if (idx <= 0 || idx == arg.length() - 1) {
                throw new IllegalArgumentException(
                        "Invalid argument '" + arg + "', expected key=value");
            }

            String key = arg.substring(0, idx);
            String value = arg.substring(idx + 1);

            if (map.containsKey(key)) {
                throw new IllegalArgumentException(
                        "Duplicate argument key: " + key);
            }

            map.put(key, value);
        }

        return map;
    }

    /**
     * Return the value for a required argument.
     *
     * @throws IllegalArgumentException if missing
     */
    public String get(String key) throws IllegalArgumentException {
        String value = args.get(key);
        if (value == null) {
            throw new IllegalArgumentException(
                    "Missing required argument: " + key);
        }
        return value;
    }

    /**
     * Return the value for an optional argument.
     */
    public String getOrDefault(String key, String defaultValue) {
        String value = args.get(key);
        return value != null ? value : defaultValue;
    }

    /**
     * Return the value for a required argument as an integer.
     *
     * @throws IllegalArgumentException if missing or not a valid integer
     */
    public int getInt(String key) throws IllegalArgumentException {
        String value = get(key);
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(
                    "Invalid integer for argument '" + key + "': " + value);
        }
    }

    /**
     * Return the value for a required argument as an integer within a range.
     *
     * @param key the argument key
     * @param min minimum allowed value (inclusive)
     * @param max maximum allowed value (inclusive)
     * @throws IllegalArgumentException if missing, not a valid integer, or out of
     *                                  range
     */
    public int getInt(String key, int min, int max) throws IllegalArgumentException {
        int value = getInt(key);
        if (value < min || value > max) {
            throw new IllegalArgumentException(
                    "Argument '" + key + "' value " + value + " is out of range [" + min + "-" + max + "]");
        }
        return value;
    }

    /**
     * Return the value for a required argument as a list of comma-separated
     * strings.
     * Each element is trimmed of leading and trailing whitespace.
     *
     * @param key the argument key
     * @return an immutable list of trimmed strings
     * @throws IllegalArgumentException if missing
     */
    public List<String> getList(String key) throws IllegalArgumentException {
        String value = get(key);
        return Collections.unmodifiableList(
                Arrays.asList(Arrays.stream(value.split(","))
                        .map(String::trim)
                        .toArray(String[]::new)));
    }

    /**
     * Return all arguments (read-only, deterministic order).
     */
    public Map<String, String> args() {
        return Collections.unmodifiableMap(args);
    }

    /**
     * Write CSV headers explicitly.
     */
    public void header() {
        csv.header();
    }

    /**
     * Write a CSV row.
     * If headers haven't been written, auto-writes headers first.
     */
    public void row(String[] values) {
        csv.row(values);
    }

    /**
     * Flush output.
     */
    public void flush() {
        csv.flush();
    }
}
