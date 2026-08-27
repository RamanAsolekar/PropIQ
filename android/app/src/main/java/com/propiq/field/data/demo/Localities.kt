package com.propiq.field.data.demo

/**
 * Locality reference data.
 *
 * Generated from backend/app/data/india_circle_rates.py so the picker can never
 * offer a locality the valuation model does not know. `PropertyInput.locality`
 * is a free-form string on the wire, but get_circle_rate() falls back to a
 * default rate for unknown names, which silently produces a wrong valuation —
 * so the app constrains the input rather than trusting it.
 *
 * Coordinates are used two ways: to pre-select the nearest locality from the GPS
 * fix, and to fill geo_lat/geo_lon when the device has no fix at all.
 */
object Localities {

    data class Entry(
        val name: String,
        val city: String,
        val zoneTier: String,
        val lat: Double,
        val lon: Double,
    )

    val all: List<Entry> = listOf(
        // ── Pune ──
        Entry("Koregaon Park", "Pune", "prime", 18.5362, 73.8938),
        Entry("Shivajinagar", "Pune", "prime", 18.5308, 73.8474),
        Entry("Baner", "Pune", "prime", 18.559, 73.7868),
        Entry("Kothrud", "Pune", "prime", 18.5074, 73.8077),
        Entry("Aundh", "Pune", "prime", 18.5578, 73.8073),
        Entry("Viman Nagar", "Pune", "prime", 18.5679, 73.9143),
        Entry("Kalyani Nagar", "Pune", "prime", 18.5456, 73.901),
        Entry("Magarpatta", "Pune", "prime", 18.5114, 73.9274),
        Entry("Bavdhan", "Pune", "prime", 18.5196, 73.7805),
        Entry("Wakad", "Pune", "mid", 18.5975, 73.7614),
        Entry("Hinjewadi", "Pune", "mid", 18.5912, 73.738),
        Entry("Hadapsar", "Pune", "mid", 18.5018, 73.926),
        Entry("Pimpri", "Pune", "mid", 18.6279, 73.7997),
        Entry("Chinchwad", "Pune", "mid", 18.6436, 73.7983),
        Entry("Katraj", "Pune", "mid", 18.4601, 73.8669),
        Entry("Kondhwa", "Pune", "mid", 18.4672, 73.8924),
        Entry("Nibm", "Pune", "mid", 18.4608, 73.898),
        Entry("Dhanori", "Pune", "mid", 18.5896, 73.9155),
        Entry("Vishrantwadi", "Pune", "mid", 18.581, 73.901),
        Entry("Ravet", "Pune", "mid", 18.6434, 73.7449),
        Entry("Wagholi", "Pune", "peripheral", 18.5617, 73.9757),
        Entry("Talegaon", "Pune", "peripheral", 18.7332, 73.6723),
        Entry("Chakan", "Pune", "peripheral", 18.7601, 73.8637),
        Entry("Ambegaon", "Pune", "peripheral", 18.4489, 73.8526),
        Entry("Undri", "Pune", "peripheral", 18.4524, 73.9009),
        Entry("Fursungi", "Pune", "peripheral", 18.4842, 73.9279),
        // ── Mumbai ──
        Entry("Bandra West", "Mumbai", "prime", 19.0596, 72.8295),
        Entry("Worli", "Mumbai", "prime", 19.0176, 72.8178),
        Entry("Powai", "Mumbai", "prime", 19.1197, 72.9051),
        Entry("Andheri West", "Mumbai", "prime", 19.1313, 72.8258),
        Entry("Andheri East", "Mumbai", "mid", 19.1136, 72.8697),
        Entry("Thane", "Mumbai", "mid", 19.2183, 72.9781),
        Entry("Navi Mumbai", "Mumbai", "mid", 19.0368, 73.0158),
        Entry("Dadar", "Mumbai", "prime", 19.0186, 72.843),
        Entry("Borivali", "Mumbai", "mid", 19.2288, 72.8563),
        Entry("Goregaon", "Mumbai", "mid", 19.1663, 72.8526),
        Entry("Malad", "Mumbai", "mid", 19.1872, 72.8484),
        Entry("Kandivali", "Mumbai", "mid", 19.2071, 72.8546),
        Entry("Kurla", "Mumbai", "mid", 19.0726, 72.8826),
        Entry("Ghatkopar", "Mumbai", "mid", 19.0867, 72.9082),
        Entry("Mulund", "Mumbai", "mid", 19.1726, 72.956),
        Entry("Chembur", "Mumbai", "mid", 19.0522, 72.8994),
        Entry("Mira Road", "Mumbai", "peripheral", 19.2815, 72.8656),
        Entry("Virar", "Mumbai", "peripheral", 19.4647, 72.8108),
        Entry("Panvel", "Mumbai", "peripheral", 18.9894, 73.1175),
        Entry("Kharghar", "Mumbai", "mid", 19.0473, 73.0687),
        // ── Bangalore ──
        Entry("Koramangala", "Bangalore", "prime", 12.9279, 77.6271),
        Entry("Indiranagar", "Bangalore", "prime", 12.9716, 77.6412),
        Entry("Whitefield", "Bangalore", "prime", 12.9698, 77.7499),
        Entry("HSR Layout", "Bangalore", "prime", 12.9082, 77.6476),
        Entry("Jayanagar", "Bangalore", "prime", 12.9259, 77.5937),
        Entry("JP Nagar", "Bangalore", "prime", 12.9067, 77.5856),
        Entry("Electronic City", "Bangalore", "mid", 12.8399, 77.677),
        Entry("Marathahalli", "Bangalore", "mid", 12.9591, 77.7001),
        Entry("Sarjapur Road", "Bangalore", "mid", 12.8954, 77.6795),
        Entry("Yelahanka", "Bangalore", "mid", 13.1004, 77.5963),
        Entry("Hebbal", "Bangalore", "mid", 13.0358, 77.597),
        Entry("Rajajinagar", "Bangalore", "mid", 12.9913, 77.556),
        Entry("Banashankari", "Bangalore", "mid", 12.9249, 77.5468),
        Entry("Bannerghatta", "Bangalore", "peripheral", 12.8624, 77.5982),
        Entry("Devanahalli", "Bangalore", "peripheral", 13.2468, 77.7137),
        Entry("Tumkur Road", "Bangalore", "peripheral", 13.0298, 77.4968),
        Entry("Kanakapura Road", "Bangalore", "peripheral", 12.8724, 77.5581),
    )

    val cities: List<String> = listOf("Pune", "Mumbai", "Bangalore")

    fun forCity(city: String): List<Entry> = all.filter { it.city == city }

    fun byName(name: String): Entry? = all.firstOrNull { it.name.equals(name, true) }

    /** name -> (lat, lon), for GeoFix.nearestLocality. */
    fun coordinateMap(city: String? = null): Map<String, Pair<Double, Double>> =
        all.filter { city == null || it.city == city }
            .associate { it.name to (it.lat to it.lon) }
}
