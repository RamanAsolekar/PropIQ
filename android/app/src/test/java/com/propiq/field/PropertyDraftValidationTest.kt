package com.propiq.field

import com.propiq.field.ui.capture.PropertyDraft
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * These bounds are not arbitrary — they mirror the Pydantic Field constraints in
 * backend/app/models/schemas.py (`size_sqft` gt 100 lt 50000, `age_years` 0..80,
 * `floor_num` 0..50).
 *
 * If the backend ever loosens or tightens those, these tests are the thing that
 * should fail, because a mismatch means the officer fills a form in a basement,
 * queues it, walks out, and only then discovers the server rejects it with a 422.
 */
class PropertyDraftValidationTest {

    private fun valid() = PropertyDraft(
        locality = "Baner",
        propType = "3bhk_apartment",
        sizeSqft = "1450",
        ageYears = "8",
        floorNum = "7",
    )

    @Test
    fun `a fully specified draft is complete`() {
        assertTrue(valid().isComplete)
    }

    @Test
    fun `blank locality blocks submission`() {
        // The valuation model silently falls back to a default circle rate for
        // an unknown locality, which produces a quietly wrong number — so an
        // empty locality must never reach the wire.
        assertFalse(valid().copy(locality = "").isComplete)
    }

    @Test
    fun `size must sit strictly inside the backend bounds`() {
        assertNotNull(valid().copy(sizeSqft = "100").sizeError)   // gt 100, exclusive
        assertNotNull(valid().copy(sizeSqft = "50000").sizeError) // lt 50000, exclusive
        assertNull(valid().copy(sizeSqft = "101").sizeError)
        assertNull(valid().copy(sizeSqft = "49999").sizeError)
    }

    @Test
    fun `age accepts the inclusive zero to eighty range`() {
        assertNull(valid().copy(ageYears = "0").ageError)
        assertNull(valid().copy(ageYears = "80").ageError)
        assertNotNull(valid().copy(ageYears = "81").ageError)
        assertNotNull(valid().copy(ageYears = "-1").ageError)
    }

    @Test
    fun `floor accepts ground through fifty`() {
        assertNull(valid().copy(floorNum = "0").floorError)
        assertNull(valid().copy(floorNum = "50").floorError)
        assertNotNull(valid().copy(floorNum = "51").floorError)
    }

    @Test
    fun `an empty field is not an error until something is typed`() {
        // Showing "Enter a number" on a pristine form is hostile; showing it on
        // a half-typed one is correct.
        assertNull(valid().copy(sizeSqft = "").sizeError)
        assertNotNull(valid().copy(sizeSqft = "abc").sizeError)
    }

    @Test
    fun `toRequest converts booleans to the ints the backend expects`() {
        // PropertyInput declares these as int Fields with ge=0 le=1, not bools.
        val req = valid().copy(
            isFreehold = true,
            hasEncumbrance = false,
            hasLegalDispute = true,
        ).toRequest(fix = null, fallbackLatLon = null)

        assertEquals(1, req.isFreehold)
        assertEquals(0, req.hasEncumbrance)
        assertEquals(1, req.hasLegalDispute)
    }

    @Test
    fun `toRequest falls back to locality coordinates when there is no GPS fix`() {
        val req = valid().toRequest(fix = null, fallbackLatLon = 18.559 to 73.7868)
        assertEquals(18.559, req.geoLat!!, 1e-6)
        assertEquals(73.7868, req.geoLon!!, 1e-6)
    }

    @Test
    fun `toRequest sends null coordinates when neither GPS nor fallback exists`() {
        // geo_lat/geo_lon are Optional server-side; null makes the backend
        // geocode instead, which is correct rather than an error.
        val req = valid().toRequest(fix = null, fallbackLatLon = null)
        assertNull(req.geoLat)
        assertNull(req.geoLon)
    }

    @Test
    fun `toRequest trims the loan reference`() {
        val req = valid().copy(loanRef = "  LAP-2026-04417  ").toRequest(null, null)
        assertEquals("LAP-2026-04417", req.loanRef)
    }

    @Test
    fun `the sample property is itself valid`() {
        // Demo Mode depends on this: a malformed sample would fail on stage.
        assertTrue(PropertyDraft.sample().isComplete)
    }
}
