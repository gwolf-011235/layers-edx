package epq.reference;

import java.io.PrintWriter;
import java.util.Objects;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public final class CsvWriter {

    private final PrintWriter out;
    private final CsvSchema schema;
    private boolean headerWritten = false;

    public CsvWriter(PrintWriter out, CsvSchema schema) {
        this.out = Objects.requireNonNull(out, "out");
        this.schema = Objects.requireNonNull(schema, "schema must not be null");
    }

    /**
     * Writes the CSV header.
     * Will be called automatically if schema is set and a row is written before
     * the header.
     *
     * @throws IllegalStateException if header has already been written
     */
    public void header() throws IllegalStateException {
        if (headerWritten) {
            throw new IllegalStateException("CSV header already written");
        }
        writeLine(this.schema.header());
        headerWritten = true;
    }

    /**
     * Writes a single CSV row.
     * If schema is set and headers haven't been written, automatically writes
     * headers first.
     */
    public void row(String[] values) {
        if (!headerWritten) {
            this.header();
        }
        writeLine(values);
    }

    /**
     * Flushes the underlying writer.
     */
    public void flush() {
        out.flush();
    }

    /**
     * Write a CSV line.
     * Escapes field values according to RFC 4180:
     * - If a field contains comma, double-quote, or newline, it is wrapped in
     * quotes
     * - Internal double-quotes are escaped by doubling them
     *
     * @param values The values for the line.
     */
    private void writeLine(String[] values) {
        String line = Stream.of(values)
                .map(this::escapeCsvField)
                .collect(Collectors.joining(","));
        out.println(line);
    }

    /**
     * Escape a single CSV field value according to RFC 4180.
     *
     * @param value The field value (may be null or empty)
     * @return The escaped field value
     */
    private String escapeCsvField(String value) {
        if (value == null || value.isEmpty()) {
            return value;
        }

        // Check if escaping is needed (contains comma, quote, or newline)
        if (value.contains(",") || value.contains("\"") || value.contains("\n")) {
            // Escape internal quotes by doubling them
            String escaped = value.replace("\"", "\"\"");
            // Wrap entire field in quotes
            return "\"" + escaped + "\"";
        }

        return value;
    }
}
