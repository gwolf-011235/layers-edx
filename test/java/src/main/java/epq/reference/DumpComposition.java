package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import java.util.List;
import gov.nist.microanalysis.EPQLibrary.Composition;
import gov.nist.microanalysis.EPQLibrary.Element;

/**
 * DumpComposition dumps properties of a material composition.
 *
 * Arguments:
 * - elements: comma-separated element symbols or atomic numbers (e.g. Fe,O or
 * 26,8)
 * - fractions: comma-separated mass fractions (must match element count, sum ~
 * 1.0)
 *
 * Output: One row per element in the composition, containing:
 * - Element name and atomic number
 * - Weight fractions (normalized and unnormalized)
 * - Atomic percent
 * - Atoms per kilogram
 */
public final class DumpComposition implements DumpModule {

  static final CsvSchema SCHEMA = new CsvSchema(
      new CsvColumn("element", STRING, false),
      new CsvColumn("atomic_number", INT, false),
      new CsvColumn("weight_fraction", DOUBLE, false),
      new CsvColumn("normalized_weight_fraction", DOUBLE, false),
      new CsvColumn("atomic_percent", DOUBLE, false),
      new CsvColumn("atoms_per_kg", DOUBLE, false));

  @Override
  public String name() {
    return "Composition";
  }

  @Override
  public String usage() {
    return "Composition elements=<symbol,list> fractions=<decimal,list>\n" +
        "  elements: comma-separated element symbols or atomic numbers (e.g. Fe,O or 26,8)\n" +
        "  fractions: comma-separated mass fractions (must match element count)";
  }

  @Override
  public CsvSchema schema() {
    return SCHEMA;
  }

  @Override
  public void run(DumpContext ctx) throws IllegalArgumentException {

    // Parse arguments using the new getList() method
    List<String> elementNames = ctx.getList("elements");
    List<String> fractionStrs = ctx.getList("fractions");

    // Validate counts match
    if (elementNames.size() != fractionStrs.size()) {
      throw new IllegalArgumentException(
          "Element count (" + elementNames.size() + ") must match fraction count (" + fractionStrs.size() + ")");
    }

    // Parse elements and fractions
    Element[] elements = new Element[elementNames.size()];
    double[] fractions = new double[fractionStrs.size()];

    for (int i = 0; i < elementNames.size(); i++) {
      String elemName = elementNames.get(i);
      Element elm = parseElement(elemName);
      if (elm == null) {
        throw new IllegalArgumentException("Unknown element: " + elemName);
      }
      elements[i] = elm;

      try {
        fractions[i] = Double.parseDouble(fractionStrs.get(i));
      } catch (NumberFormatException e) {
        throw new IllegalArgumentException(
            "Invalid fraction at index " + i + ": " + fractionStrs.get(i));
      }
    }

    // Create composition
    Composition comp = new Composition(elements, fractions);

    // Emit one row per element
    for (Element elm : comp.getElementSet()) {
      CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);
      rowBuilder
          .set("element", elm.toAbbrev())
          .set("atomic_number", elm.getAtomicNumber())
          .set("weight_fraction", comp.weightFraction(elm, false))
          .set("normalized_weight_fraction", comp.weightFraction(elm, true))
          .set("atomic_percent", comp.atomicPercent(elm))
          .set("atoms_per_kg", comp.atomsPerKg(elm, true));

      ctx.row(rowBuilder.buildRow());
    }

    ctx.flush();
  }

  /**
   * Parse an element from a string, which can be:
   * - An element symbol (Fe, Au, Si)
   * - An atomic number as string (26, 79, 14)
   *
   * @return the Element, or null if not found
   */
  private static Element parseElement(String input) {
    // Try parsing as atomic number first
    try {
      int z = Integer.parseInt(input);
      if (z >= 1 && z < Element.elmEndOfElements) {
        return Element.byAtomicNumber(z);
      }
      return null;
    } catch (NumberFormatException e) {
      // Not a number, try by name
    }

    // Try by symbol only
    return Element.byAbbrev(input);
  }
}
