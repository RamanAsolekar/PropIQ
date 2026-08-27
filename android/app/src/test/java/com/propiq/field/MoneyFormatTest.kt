package com.propiq.field

import com.propiq.field.core.Fmt
import com.propiq.field.core.Money
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * The hero number on the results screen is the single thing a jury reads in the
 * first three seconds, and Indian digit grouping is not what Java's default
 * NumberFormat does. These pin the formatting so a refactor cannot quietly turn
 * "₹1.94 Cr" into "₹19,400,000".
 */
class MoneyFormatTest {

    @Test
    fun `compact uses crore above one crore`() {
        assertEquals("₹1.94 Cr", Money.compact(19_400_000))
        assertEquals("₹1 Cr", Money.compact(10_000_000))
        assertEquals("₹12.5 Cr", Money.compact(125_000_000))
    }

    @Test
    fun `compact uses lakh between one lakh and one crore`() {
        assertEquals("₹5 L", Money.compact(500_000))
        assertEquals("₹68.8 L", Money.compact(6_880_000))
        // Boundary: one rupee under a crore must not round up into "Cr"
        assertEquals("₹99.99 L", Money.compact(9_999_000))
    }

    @Test
    fun `compact handles thousands and small values`() {
        assertEquals("₹13.38 K", Money.compact(13_379))
        assertEquals("₹500", Money.compact(500))
        assertEquals("₹0", Money.compact(0))
    }

    @Test
    fun `compact renders null as an em dash rather than crashing`() {
        // Every DTO field is nullable because the backend attaches blocks
        // "additively, non-fatal" — the formatter must absorb that.
        assertEquals("—", Money.compact(null))
        assertEquals("—", Money.full(null))
        assertEquals("—", Money.range(null))
    }

    @Test
    fun `compact keeps the sign on negative values`() {
        // Negative SHAP driver impacts flow through this same formatter.
        assertEquals("-₹8.2 L", Money.compact(-820_000))
    }

    @Test
    fun `full uses Indian digit grouping not western`() {
        // 19400000 is 1,94,00,000 in India — NOT 19,400,000.
        assertEquals("₹1,94,00,000", Money.full(19_400_000))
        assertEquals("₹10,800", Money.full(10_800))
        assertEquals("₹100", Money.full(100))
    }

    @Test
    fun `range joins both ends compactly`() {
        assertEquals("₹1.74 Cr – ₹2.13 Cr", Money.range(listOf(17_400_000, 21_260_000)))
        // A malformed one-element range must not throw.
        assertEquals("—", Money.range(listOf(17_400_000)))
    }

    @Test
    fun `propType humanises the backend enum`() {
        assertEquals("3BHK Apartment", Fmt.propType("3bhk_apartment"))
        assertEquals("Warehouse", Fmt.propType("warehouse"))
        assertEquals("—", Fmt.propType(null))
    }

    @Test
    fun `flagLabel keeps domain acronyms uppercase`() {
        assertEquals("CV Property Type Mismatch", Fmt.flagLabel("cv_property_type_mismatch"))
        assertEquals("RBI Ceiling", Fmt.flagLabel("rbi_ceiling"))
        assertEquals("Risk flag", Fmt.flagLabel(null))
    }
}
