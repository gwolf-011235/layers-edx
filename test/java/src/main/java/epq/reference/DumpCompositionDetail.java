package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import java.util.List;
import gov.nist.microanalysis.EPQLibrary.Composition;
import gov.nist.microanalysis.EPQLibrary.Element;

/**
 * DumpCompositionDetail dumps per-element properties of a material composition.
 *
 * Arguments:
 * - elements: comma-separated element symbols or atomic numbers (e.g. Fe,O or
 * 26,8)
 * - fractions: comma-separated mass fractions (must match element count, sum ~
 * 1.0)
 *
 * Output: One row per element in the composition, containing:
 * - Element name and atomic number
 * - Weight fractions (normalized and unnormalized) with uncertainties
 * - Atomic percent with uncertainty
 * - Atoms per kilogram with uncertainty
 * - Stoichiometry (atomic fraction) with uncertainty
 */
public final class DumpCompositionDetail implements DumpModule {

  static final CsvSchema SCHEMA = new CsvSchema(
      new CsvColumn("element", STRING, false),
      new CsvColumn("atomic_number", INT, false),
      new CsvColumn("weight_fraction", DOUBLE, false),
      new CsvColumn("weight_fraction_sigma", DOUBLE, true),
      new CsvColumn("normalized_weight_fraction", DOUBLE, false),
      new CsvColumn("normalized_weight_fraction_sigma", DOUBLE, true),
      new CsvColumn("atomic_percent", DOUBLE, false),
      new CsvColumn("atomic_percent_sigma", DOUBLE, true),
      new CsvColumn("atoms_per_kg", DOUBLE, false),
      new CsvColumn("atoms_per_kg_sigma", DOUBLE, true),
      new CsvColumn("stoichiometry", DOUBLE, false),
      new CsvColumn("stoichiometry_sigma", DOUBLE, true));

  @Override
  public String name() {
    return "CompositionDetail";
  }

  @Override
  public String usage() {
    return "CompositionDetail elements=<symbol,list> fractions=<decimal,list> [mode=weight|mole]\n" +
        "  elements: comma-separated element symbols or atomic numbers (e.g. Fe,O or 26,8)\n" +
        "  fractions: comma-separated fractions (must match element count)\n" +
        "  mode: fraction type - 'weight' (default) or 'mole' for stoichiometric";
  }

  @Override
  public CsvSchema schema() {
    return SCHEMA;
  }

  @Override
  public void run(DumpContext ctx) throws IllegalArgumentException {

    // Parse arguments
    final List<String> elementNames = ctx.getList("elements");
    final List<String> fractionStrs = ctx.getList("fractions");
    final String mode = ctx.getOrDefault("mode", "weight").toLowerCase();


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
      Element elm = DumpUtils.parseElement(elemName);
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

    // Create composition based on mode
    Composition comp;

    if (mode.equals("mole")) {
      comp = new Composition();
      comp.defineByMoleFraction(elements, fractions);
    } else if (mode.equals("weight")) {
      comp = new Composition(elements, fractions);
    } else {
      throw new IllegalArgumentException(
          "Invalid mode: " + mode + ". Must be 'weight' or 'mole'");
    }

    // Emit one row per element
    for (Element elm : comp.getElementSet()) {
      CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);

      // Get properties with uncertainties
      var wfU = comp.weightFractionU(elm, false);
      var nwfU = comp.weightFractionU(elm, true);
      var apU = comp.atomicPercentU(elm);
      var apkgU = comp.atomsPerKgU(elm, true);
      var stoichU = comp.stoichiometryU(elm);

      // Extract nominal values and uncertainties
      rowBuilder
          .set("element", elm.toAbbrev())
          .set("atomic_number", elm.getAtomicNumber())
          .set("weight_fraction", wfU.doubleValue())
          .set("weight_fraction_sigma", DumpUtils.sigma(wfU))
          .set("normalized_weight_fraction", nwfU.doubleValue())
          .set("normalized_weight_fraction_sigma", DumpUtils.sigma(nwfU))
          .set("atomic_percent", apU.doubleValue())
          .set("atomic_percent_sigma", DumpUtils.sigma(apU))
          .set("atoms_per_kg", apkgU.doubleValue())
          .set("atoms_per_kg_sigma", DumpUtils.sigma(apkgU))
          .set("stoichiometry", stoichU.doubleValue())
          .set("stoichiometry_sigma", DumpUtils.sigma(stoichU));

      ctx.row(rowBuilder.buildRow());
    }

    ctx.flush();
  }
}
