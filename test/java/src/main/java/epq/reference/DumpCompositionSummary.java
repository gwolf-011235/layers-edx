package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import java.util.List;
import gov.nist.microanalysis.EPQLibrary.Composition;
import gov.nist.microanalysis.EPQLibrary.Element;

/**
 * DumpCompositionSummary dumps aggregate properties of a material composition.
 *
 * Arguments:
 * - elements: comma-separated element symbols or atomic numbers (e.g. Fe,O or
 * 26,8)
 * - fractions: comma-separated mass fractions (must match element count, sum ~
 * 1.0)
 *
 * Output: Single row containing whole-composition properties:
 * - Number of elements
 * - Weight-averaged atomic number (with uncertainty)
 * - Mean atomic number (with uncertainty)
 * - Sum of weight fractions (with uncertainty)
 * - Optimal representation (STOICIOMETRY, WEIGHT_PCT, UNDETERMINED)
 * - Whether composition contains uncertainties
 * - Composition name (if set)
 */
public final class DumpCompositionSummary implements DumpModule {

  static final CsvSchema SCHEMA = new CsvSchema(
      new CsvColumn("element_count", INT, false),
      new CsvColumn("weight_avg_atomic_number", DOUBLE, false),
      new CsvColumn("weight_avg_atomic_number_sigma", DOUBLE, true),
      new CsvColumn("mean_atomic_number", DOUBLE, false),
      new CsvColumn("mean_atomic_number_sigma", DOUBLE, true),
      new CsvColumn("sum_weight_fraction", DOUBLE, false),
      new CsvColumn("sum_weight_fraction_sigma", DOUBLE, true),
      new CsvColumn("optimal_representation", STRING, false),
      new CsvColumn("is_uncertain", BOOL, false),
      new CsvColumn("name", STRING, true));

  @Override
  public String name() {
    return "CompositionSummary";
  }

  @Override
  public String usage() {
    return "CompositionSummary elements=<symbol,list> fractions=<decimal,list>\n" +
        "  elements: comma-separated element symbols or atomic numbers (e.g. Fe,O or 26,8)\n" +
        "  fractions: comma-separated mass fractions (must match element count)";
  }

  @Override
  public CsvSchema schema() {
    return SCHEMA;
  }

  @Override
  public void run(DumpContext ctx) throws IllegalArgumentException {

    // Parse arguments
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

    // Get aggregate properties with uncertainties
    var wavgU = comp.weightAvgAtomicNumberU();
    var meanU = comp.meanAtomicNumberU();
    var sumU = comp.sumWeightFractionU();

    // Build and emit single row
    CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);
    rowBuilder
        .set("element_count", comp.getElementCount())
        .set("weight_avg_atomic_number", wavgU.doubleValue())
        .set("weight_avg_atomic_number_sigma", sigma(wavgU))
        .set("mean_atomic_number", meanU.doubleValue())
        .set("mean_atomic_number_sigma", sigma(meanU))
        .set("sum_weight_fraction", sumU.doubleValue())
        .set("sum_weight_fraction_sigma", sigma(sumU))
        .set("optimal_representation", comp.getOptimalRepresentation().name())
        .set("is_uncertain", comp.isUncertain())
        .set("name", comp.getName());

    ctx.row(rowBuilder.buildRow());
    ctx.flush();
  }

  /**
   * Extract uncertainty (sigma) from UncertainValue2, returning null if zero.
   *
   * @param uv the UncertainValue2 object
   * @return the uncertainty value or null if uncertainty is zero or unavailable
   */
  private static Double sigma(gov.nist.microanalysis.Utility.UncertainValue2 uv) {
    double unc = uv.uncertainty();
    return unc > 0.0 ? unc : null;
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
