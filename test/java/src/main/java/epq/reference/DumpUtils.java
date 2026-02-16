package epq.reference;

import gov.nist.microanalysis.EPQLibrary.Element;
import gov.nist.microanalysis.Utility.UncertainValue2;

/**
 * Utility methods for dump modules, such as parsing elements and extracting
 * uncertainties.
 */
public final class DumpUtils {

  private DumpUtils() {
    // Prevent instantiation
  }

  /**
   * Extract uncertainty (sigma) from UncertainValue2, returning null if zero.
   *
   * @param uv the UncertainValue2 object
   * @return the uncertainty value or null if uncertainty is zero or unavailable
   */
  public static Double sigma(UncertainValue2 uv) {
    double unc = uv.uncertainty();
    return unc > 0.0 ? unc : null;
  }

  /**
   * Parse an element from a string, which can be:
   * - An element symbol (Fe, Au, Si)
   * - An atomic number as string (26, 79, 14)
   *
   * @param input the element symbol or atomic number
   * @return the Element, or null if not found
   */
  public static Element parseElement(String input) {
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

    // Try by symbol
    return Element.byAbbrev(input);
  }
}
