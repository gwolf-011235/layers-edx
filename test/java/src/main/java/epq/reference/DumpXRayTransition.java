package epq.reference;

import static epq.reference.CsvColumn.Type.*;

import gov.nist.microanalysis.EPQLibrary.AtomicShell;
import gov.nist.microanalysis.EPQLibrary.EPQException;
import gov.nist.microanalysis.EPQLibrary.Element;
import gov.nist.microanalysis.EPQLibrary.XRayTransition;

public final class DumpXRayTransition implements DumpModule {

    static final CsvSchema SCHEMA = new CsvSchema(
            new CsvColumn("Z", INT, false),
            new CsvColumn("transition_index", INT, false),
            new CsvColumn("transition_name", STRING, false),
            new CsvColumn("source_shell", STRING, false),
            new CsvColumn("destination_shell", STRING, false),
            new CsvColumn("family", STRING, false),
            new CsvColumn("is_well_known", BOOL, false),
            new CsvColumn("exists", BOOL, true),
            new CsvColumn("energy", DOUBLE, true),
            new CsvColumn("edge_energy_eV", DOUBLE, true),
            new CsvColumn("weight_default", DOUBLE, true),
            new CsvColumn("weight_family", DOUBLE, true),
            new CsvColumn("weight_destination", DOUBLE, true),
            new CsvColumn("weight_klm", DOUBLE, true));

    @Override
    public String name() {
        return "XRayTransition";
    }

    @Override
    public String usage() {
        return "XRayTransition Z=<atomic number> trans=<transition index>";
    }

    @Override
    public CsvSchema schema() {
        return SCHEMA;
    }

    @Override
    public void run(DumpContext ctx) throws IllegalArgumentException {

        CsvRowBuilder rowBuilder = new CsvRowBuilder(SCHEMA);

        final int Z = ctx.getInt("Z", 1, Element.elmEndOfElements - 1);
        final int trans = ctx.getInt("trans", 0, XRayTransition.Last - 1);

        final Element el = Element.byAtomicNumber(Z);

        final XRayTransition xrt = new XRayTransition(el, trans);
        final boolean isWellKnown = xrt.isWellKnown();

        rowBuilder
                .set("Z", Z)
                .set("transition_index", trans)
                .set("transition_name", xrt.getSiegbahnName())
                .set("source_shell", AtomicShell.getSiegbahnName(xrt.getSourceShell()))
                .set("destination_shell", AtomicShell.getSiegbahnName(xrt.getDestinationShell()))
                .set("family", AtomicShell.getFamilyName(xrt.getFamily()))
                .set("is_well_known", isWellKnown);

        if (!isWellKnown) {
            ctx.row(rowBuilder.buildRow());
            ctx.flush();
            return;
        }

        Boolean exists = null;
        try {
            exists = xrt.exists();
        } catch (ArrayIndexOutOfBoundsException e) {
            // Shell index out of bounds for element
        }
        rowBuilder.set("exists", exists);

        if (exists == null || !exists) {
            ctx.row(rowBuilder.buildRow());
            ctx.flush();
            return;
        }

        try {
            rowBuilder
                    .set("energy", xrt.getEnergy())
                    .set("edge_energy_eV", xrt.getEdgeEnergy())
                    .set("weight_default", xrt.getWeight(XRayTransition.NormalizeDefault))
                    .set("weight_family", xrt.getWeight(XRayTransition.NormalizeFamily))
                    .set("weight_destination", xrt.getWeight(XRayTransition.NormalizeDestination))
                    .set("weight_klm", xrt.getWeight(XRayTransition.NormalizeKLM));

        } catch (EPQException e) {
            throw new IllegalArgumentException("Error retrieving transition data: " + e.getMessage());
        }

        ctx.row(rowBuilder.buildRow());
        ctx.flush();

    }

}
