package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import gov.nist.microanalysis.EPQLibrary.AtomicShell;
import gov.nist.microanalysis.EPQLibrary.Element;
import gov.nist.microanalysis.EPQLibrary.EPQFatalException;

public final class DumpAtomicShell implements DumpModule {

  static final CsvSchema SCHEMA = new CsvSchema(
      new CsvColumn("Z", INT, false),
      new CsvColumn("shell_index", INT, false),
      new CsvColumn("shell_name_siegbahn", STRING, false),
      new CsvColumn("shell_name_iupac", STRING, false),
      new CsvColumn("shell_name_atomic", STRING, false),
      new CsvColumn("family", STRING, false),
      new CsvColumn("principal_quantum_number", INT, false),
      new CsvColumn("orbital_angular_momentum", INT, false),
      new CsvColumn("total_angular_momentum", DOUBLE, false),
      new CsvColumn("capacity", INT, false),
      new CsvColumn("exists", BOOL, true),
      new CsvColumn("ground_state_occupancy", INT, true),
      new CsvColumn("edge_energy_ev", DOUBLE, true),
      new CsvColumn("energy_J", DOUBLE, true));

  @Override
  public String name() {
    return "AtomicShell";
  }

  @Override
  public String usage() {
    return "AtomicShell Z=<atomic number> shell_index=<shell index 0-48>";
  }

  @Override
  public CsvSchema schema() {
    return SCHEMA;
  }

  @Override
  public void run(DumpContext ctx) throws IllegalArgumentException {

    CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);

    final int Z = ctx.getInt("Z", 1, 118);
    final int shellIndex = ctx.getInt("shell_index", 0, AtomicShell.Last - 1);

    final Element element = Element.byAtomicNumber(Z);
    final AtomicShell shell = new AtomicShell(element, shellIndex);

    // Get shell names
    final String siegbahnName = AtomicShell.getSiegbahnName(shellIndex);
    final String iupacName = AtomicShell.getIUPACName(shellIndex);
    final String atomicName = AtomicShell.getAtomicName(shellIndex);

    // Get family name
    final int familyInt = AtomicShell.getFamily(shellIndex);
    final String familyName = AtomicShell.getFamilyName(familyInt);

    // Get quantum numbers, structure and capacity
    final int principalQuantumNumber = AtomicShell.getPrincipalQuantumNumber(shellIndex);
    final int orbitalAngularMomentum = shell.getOrbitalAngularMomentum();
    final double totalAngularMomentum = shell.getTotalAngularMomentum();
    final int capacity = shell.getCapacity();

    rowBuilder
    .set("Z", Z)
    .set("shell_index", shellIndex)
    .set("shell_name_siegbahn", siegbahnName)
    .set("shell_name_iupac", iupacName)
    .set("shell_name_atomic", atomicName)
    .set("family", familyName)
    .set("principal_quantum_number", principalQuantumNumber)
    .set("orbital_angular_momentum", orbitalAngularMomentum)
    .set("total_angular_momentum", totalAngularMomentum)
    .set("capacity", capacity);

    // check if shell exists for element
    Boolean exists = null;
    try {
      exists = shell.exists();
    } catch (ArrayIndexOutOfBoundsException e) {
      // Shell index out of bounds for element
    }
    rowBuilder.set("exists", exists);

    if (exists == null || !exists) {
      ctx.row(rowBuilder.buildRow());
      ctx.flush();
      return;
    }

    // Get capacity and occupancy
    Integer groundStateOccupancy = null;
    try {
      groundStateOccupancy = shell.getGroundStateOccupancy();
    } catch (ArrayIndexOutOfBoundsException e) {
      // Shell index out of bounds for ground state occupancy
    }

    // Get energies (nullable)
    Double edgeEnergy = null;
    try {
      edgeEnergy = shell.getEdgeEnergy();
    } catch (ArrayIndexOutOfBoundsException e) {
      // Shell index out of bounds for edge energy
    }

    Double energy = null;
    try {
      energy = shell.getEnergy();
    } catch (ArrayIndexOutOfBoundsException e) {
      // Shell index out of bounds for energy
    } catch (EPQFatalException e) {
      // EPQ may throw exception if ionization energy for element is not available
    }
    if (energy != null && Double.isNaN(energy)) {
      energy = null;
    }

    rowBuilder
        .set("ground_state_occupancy", groundStateOccupancy)
        .set("edge_energy_ev", edgeEnergy)
        .set("energy_J", energy);

    ctx.row(rowBuilder.buildRow());
    ctx.flush();
  }

}
