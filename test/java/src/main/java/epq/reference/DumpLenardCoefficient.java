package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import gov.nist.microanalysis.EPQLibrary.Element;
import gov.nist.microanalysis.EPQLibrary.FromSI;
import gov.nist.microanalysis.EPQLibrary.LenardCoefficient;
import gov.nist.microanalysis.EPQLibrary.ToSI;
import gov.nist.microanalysis.EPQLibrary.XRayTransition;

public final class DumpLenardCoefficient implements DumpModule {

  static final CsvSchema SCHEMA = new CsvSchema(
      new CsvColumn("beam_energy_kev", DOUBLE, false),
      new CsvColumn("Z", INT, false),
      new CsvColumn("transition_index", INT, false),
      new CsvColumn("algorithm", STRING, false),
      new CsvColumn("exists", BOOL, false),
      new CsvColumn("edge_energy_kev", DOUBLE, true),
      new CsvColumn("coefficient", DOUBLE, true));

  @Override
  public String name() {
    return "LenardCoefficient";
  }

  @Override
  public String usage() {
    return "LenardCoefficient beam_energy=<keV> Z=<atomic number> trans=<transition index> [algo=Heinrich|DuncumbShields|Citzaf]";
  }

  @Override
  public CsvSchema schema() {
    return SCHEMA;
  }

  @Override
  public void run(DumpContext ctx) throws IllegalArgumentException {

    CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);

    // Parse arguments
    final String beamEnergyStr = ctx.get("beam_energy");
    final double beamEnergyKeV;
    try {
      beamEnergyKeV = Double.parseDouble(beamEnergyStr);
      if (beamEnergyKeV < 0.1 || beamEnergyKeV > 1000.0) {
        throw new IllegalArgumentException(
            String.format("beam_energy must be between 0.1 and 1000.0 keV, got: %.3f", beamEnergyKeV));
      }
    } catch (NumberFormatException e) {
      throw new IllegalArgumentException(
          String.format("Invalid beam_energy value: %s", beamEnergyStr));
    }

    final int Z = ctx.getInt("Z", 1, Element.elmEndOfElements - 1);
    final int trans = ctx.getInt("trans", 0, XRayTransition.Last - 1);
    final String algoName = ctx.getOrDefault("algo", "Heinrich");

    // Create element and transition
    final Element element = Element.byAtomicNumber(Z);
    final XRayTransition xrt = new XRayTransition(element, trans);

    // Select algorithm
    final LenardCoefficient algorithm;
    switch (algoName) {
      case "Heinrich":
        algorithm = LenardCoefficient.Heinrich;
        break;
      case "DuncumbShields":
        algorithm = LenardCoefficient.DuncumbShields;
        break;
      case "Citzaf":
        algorithm = LenardCoefficient.Citzaf;
        break;
      default:
        throw new IllegalArgumentException(
            String.format("Unknown algorithm: %s (valid: Heinrich, DuncumbShields, Citzaf)", algoName));
    }

    // Convert beam energy to Joules
    final double beamEnergyJoules = ToSI.keV(beamEnergyKeV);

    // Build row with basic fields
    rowBuilder
        .set("beam_energy_kev", beamEnergyKeV)
        .set("Z", Z)
        .set("transition_index", trans)
        .set("algorithm", algoName);

    // Check if transition exists
    final boolean exists = xrt.exists();
    rowBuilder.set("exists", exists);

    if (!exists) {
      ctx.row(rowBuilder.buildRow());
      ctx.flush();
      return;
    }

    // Compute coefficient and edge energy for valid transitions
    final double edgeEnergyKeV = FromSI.keV(xrt.getEdgeEnergy());
    final double coefficient = algorithm.compute(beamEnergyJoules, xrt);

    // Add computed fields
    rowBuilder
        .set("edge_energy_kev", edgeEnergyKeV)
        .set("coefficient", coefficient);

    ctx.row(rowBuilder.buildRow());
    ctx.flush();
  }
}
