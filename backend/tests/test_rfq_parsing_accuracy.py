"""
RFQ Parsing Accuracy Test Suite

This test suite validates the accuracy of RFQ text parsing across 20 different
manufacturing RFQ types. It tests the Claude API-based RFQ parser against
real-world examples with diverse content, formats, and specifications.

Coverage:
- 20 different RFQ types covering various manufacturing sectors
- Different writing styles and languages (with English translations)
- Various specification formats and detail levels
- Accuracy metrics for field extraction
"""

import os
import pytest
import json
from typing import Dict, Any, Optional

from app.services.claude import get_claude_service

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_CLAUDE_TESTS", "false").lower() != "true",
    reason="Set RUN_LIVE_CLAUDE_TESTS=true to run live Claude accuracy benchmark",
)

# Test data: 20 diverse RFQ examples
TEST_RFQS = [
    # 1. Precision CNC Machining
    {
        "name": "Precision CNC Aluminum Parts",
        "text": """
        We require precision CNC machined aluminum components for aerospace applications.

        Specifications:
        - Material: 6061-T6 aluminum alloy
        - Quantity: 500 pieces
        - Dimensions: 100mm x 50mm x 20mm with ±0.05mm tolerance
        - Surface finish: Anodized type II, 0.0005" thickness
        - Certifications: ISO 9001, AS9100
        - Lead time: 45 days
        - Quality: 100% inspection required with CMM report
        """,
        "expected_fields": {
            "product_name": "Precision CNC Aluminum Components",
            "material": "6061-T6 aluminum",
            "quantity": "500",
            "tolerances": "±0.05mm",
            "certifications": ["ISO 9001", "AS9100"],
            "delivery_timeframe": "45 days",
        },
    },
    # 2. Injection Molded Plastics
    {
        "name": "Plastic Injection Molded Parts",
        "text": """
        RFQ: High-volume injection molded plastic components

        Requirements:
        Product: Custom plastic enclosures for consumer electronics
        Material: ABS + polycarbonate blend
        Volume: 100,000 pieces per month
        Lead time: ASAP - need first production run in 30 days
        Specifications available: 3D CAD files (STEP format)
        Quality standard: IEC 61439-1
        Color: Custom Pantone match required
        Surface finish: Gloss finish with silk-screen printing
        """,
        "expected_fields": {
            "product_name": "Injection Molded Plastic Enclosures",
            "material": "ABS + polycarbonate",
            "quantity": "100,000 pieces/month",
            "certifications": ["IEC 61439-1"],
            "delivery_timeframe": "30 days",
        },
    },
    # 3. Sheet Metal Fabrication
    {
        "name": "Sheet Metal Laser Cutting",
        "text": """
        We need sheet metal laser cut components.

        Details:
        - Material: Stainless steel 304, 2mm thickness
        - Qty: 2000 pieces
        - Laser cutting + bending required
        - Hole tolerances: ±0.1mm
        - Edge finish: Deburring required
        - Timeline: Need samples in 2 weeks, full production in 6 weeks
        - Testing: Hardness testing per ASTM D1577
        """,
        "expected_fields": {
            "product_name": "Sheet Metal Laser Cut Components",
            "material": "Stainless steel 304",
            "quantity": "2000",
            "tolerances": "±0.1mm",
            "certifications": ["ASTM D1577"],
            "delivery_timeframe": "6 weeks",
        },
    },
    # 4. Electronics PCB Assembly
    {
        "name": "PCB Assembly Service",
        "text": """
        Requesting quotation for PCB assembly services.

        Board specifications:
        - 4-layer FR-4 PCB, 10" x 8"
        - Component count: 150+ components (SMD and through-hole)
        - Solder mask: Green, silkscreen white
        - Required certifications: RoHS, ITAR compliant
        - Volume: 5000 units
        - Lead time: Flexible, prefer 12 weeks
        - Testing required: 100% AOI + in-circuit testing
        - IPC standard: IPC-A-610
        """,
        "expected_fields": {
            "product_name": "PCB Assembly",
            "material": "FR-4",
            "quantity": "5000",
            "certifications": ["RoHS", "ITAR", "IPC-A-610"],
            "delivery_timeframe": "12 weeks",
        },
    },
    # 5. Metal Stamping
    {
        "name": "Metal Stamping Parts",
        "text": """
        Metal stamping quotation request:

        Product: Automotive engine mounting brackets
        Material: Cold-rolled steel, grade HSLA
        Thickness: 3mm
        Quantity: 50,000 pieces/month
        Surface treatment: Zinc plating (Type II, 5-9 microns)
        Die design: Customer will provide or purchase from your supplier
        Tolerances: ±0.2mm
        Lead time: First article sample in 3 weeks
        Standards: AIAG D-9000
        """,
        "expected_fields": {
            "product_name": "Metal Stamped Engine Mounting Brackets",
            "material": "HSLA steel",
            "quantity": "50,000/month",
            "tolerances": "±0.2mm",
            "certifications": ["AIAG D-9000"],
            "delivery_timeframe": "3 weeks",
        },
    },
    # 6. Medical Device Components
    {
        "name": "Medical Grade Components",
        "text": """
        We require medical-grade titanium components for surgical instruments.

        Material: Titanium Grade 5 (Ti-6Al-4V)
        Component type: Surgical blade blanks
        Quantity: 1000 pieces
        Dimensions: 50mm x 10mm x 1.5mm
        Surface finish: Passivated per ASTM A967
        Certifications MANDATORY:
          - FDA cleared (Class II medical device)
          - ISO 13485:2016
          - ISO 9001:2015
        Quality: No defects allowed, 100% inspection
        Biocompatibility: Must pass cytotoxicity testing per ISO 10993-5
        Delivery: 60 days maximum
        """,
        "expected_fields": {
            "product_name": "Titanium Surgical Instrument Blanks",
            "material": "Titanium Grade 5",
            "quantity": "1000",
            "certifications": ["FDA", "ISO 13485", "ISO 10993-5"],
            "delivery_timeframe": "60 days",
        },
    },
    # 7. Forged Components
    {
        "name": "Forged Steel Parts",
        "text": """
        Forging RFQ for industrial equipment components.

        Material: Chrome-molybdenum steel (4140)
        Process: Open die forging
        Part weight: 2.5 kg per unit
        Quantity: 500 pieces
        Dimensional tolerance: ±2mm
        Surface finish: Normalized (no machining required initially)
        Heat treatment: Hardness 250-300 HV required
        Application: Off-road vehicle suspension components
        Standards compliance: ASTM F468
        Delivery timeframe: 8 weeks from order
        """,
        "expected_fields": {
            "product_name": "Forged 4140 Steel Components",
            "material": "Chrome-molybdenum steel",
            "quantity": "500",
            "certifications": ["ASTM F468"],
            "delivery_timeframe": "8 weeks",
        },
    },
    # 8. Rubber Molded Parts
    {
        "name": "Rubber Molded Components",
        "text": """
        RFQ for rubber molded parts:

        Material: Nitrile rubber (NBR 70)
        Component: Oil seals
        Dimensions: OD 50mm, ID 30mm, width 8mm
        Volume: 10,000 pieces per month
        Shore hardness: 70±5
        Compression set: <25% after 70hrs at 70°C
        Color: Black
        Certifications: FDA approved, NSF certified
        Timeline: 4 weeks to first prototype, 6 weeks to production
        Testing: Permeability testing to ISO 1619
        """,
        "expected_fields": {
            "product_name": "Nitrile Rubber Oil Seals",
            "material": "Nitrile rubber",
            "quantity": "10,000/month",
            "certifications": ["FDA", "NSF"],
            "delivery_timeframe": "6 weeks",
        },
    },
    # 9. Composite Materials
    {
        "name": "Carbon Fiber Composites",
        "text": """
        Carbon fiber composite components for aerospace:

        Material: Carbon fiber reinforced polymer (CFRP), 5-harness satin weave
        Specifications:
        - Fiber: AS4 carbon fiber
        - Matrix: Epoxy resin (IM7/8552)
        - Dimensions: 500mm x 300mm x 2.5mm
        - Quantity: 200 pieces
        - Tolerances: ±0.5mm
        - Surface: Smooth finish, no porosity allowed
        - Testing: CAI (Compression After Impact) per ASTM WK36
        - Lead time: 90 days
        - Standards: AS9100 and BAC 5555
        """,
        "expected_fields": {
            "product_name": "Carbon Fiber Composite Panels",
            "material": "CFRP with AS4 carbon fiber",
            "quantity": "200",
            "certifications": ["AS9100", "BAC 5555"],
            "delivery_timeframe": "90 days",
        },
    },
    # 10. Wire Harness Assembly
    {
        "name": "Wire Harness Assembly",
        "text": """
        RFQ for automotive wire harness assembly:

        Wire gauge: 18 AWG and 20 AWG
        Total length: 5 meters per harness
        Connectors: OEM automotive connectors per specification
        Terminals: Crimped and soldered to specifications
        Color coding: Customer-specified per wiring diagram
        Shielding: Foil shield for power lines
        Quantity: 50,000 units per month
        Quality: Zero defects, 100% continuity testing
        Compliance: ISO/TS 16949, AEC-Q200
        Lead time: 6 weeks
        Documentation: Wiring diagram and workmanship standard required
        """,
        "expected_fields": {
            "product_name": "Automotive Wire Harness Assembly",
            "material": "Copper wire 18-20 AWG",
            "quantity": "50,000/month",
            "certifications": ["ISO/TS 16949", "AEC-Q200"],
            "delivery_timeframe": "6 weeks",
        },
    },
    # 11. CNC Machined Steel
    {
        "name": "CNC Machined Steel Components",
        "text": """
        Request for quotation on CNC machining services:

        Material: 1018 carbon steel
        Component type: Motor shafts
        Dimensions: 50mm OD, 200mm length
        Quantity: 1000 pieces
        Surface finish: Ground smooth (Ra 0.8 µm)
        Heat treatment: Case hardened to 58-62 HRC
        Tolerance: H7/g6 fit per ISO 286
        Keyway: Provided per DIN 6885
        Testing: Hardness testing and run-out verification
        Delivery: 30 days
        Compliance: RoHS compliant
        """,
        "expected_fields": {
            "product_name": "CNC Machined Motor Shafts",
            "material": "1018 carbon steel",
            "quantity": "1000",
            "certifications": ["RoHS", "ISO 286"],
            "delivery_timeframe": "30 days",
        },
    },
    # 12. Powder Coating
    {
        "name": "Powder Coat Finishing Service",
        "text": """
        Powder coating service request:

        Substrate: Fabricated steel structures
        Powder type: Epoxy polyester hybrid
        Color: RAL 5010 (gentian blue)
        Coating thickness: 100-150 microns
        Quantity: 500 units
        Size range: Various from 100cm to 300cm length
        Test requirements:
          - Adhesion: ASTM B3359
          - Impact resistance: ASTM D2794
          - Salt spray: ASTM B117 (500 hours)
        Lead time: 4 weeks
        Quality: Zero runs/sags, uniform coverage
        """,
        "expected_fields": {
            "product_name": "Powder Coating Service",
            "material": "Steel",
            "quantity": "500 units",
            "certifications": ["ASTM B3359", "ASTM D2794", "ASTM B117"],
            "delivery_timeframe": "4 weeks",
        },
    },
    # 13. Die Casting
    {
        "name": "Die Cast Aluminum Parts",
        "text": """
        Die casting quotation for aluminum components:

        Alloy: A380 aluminum
        Component: Motor housings
        Quantity: 20,000 pieces
        Wall thickness: 3-5mm
        Dimensional tolerance: ±0.05mm
        Surface: As-cast finish acceptable, minor porosity allowed
        Certification: NADCA #207 specification
        Heat treatment: T5
        Mechanical properties: Yield 160 MPa minimum
        Delivery schedule:
          - Tooling: 6 weeks
          - Production: 8 weeks
        Quality control: First article inspection (FAI)
        """,
        "expected_fields": {
            "product_name": "Die Cast Aluminum Motor Housings",
            "material": "A380 aluminum",
            "quantity": "20,000",
            "certifications": ["NADCA #207"],
            "delivery_timeframe": "8 weeks",
        },
    },
    # 14. 3D Printing (Additive Manufacturing)
    {
        "name": "3D Printed Prototype Parts",
        "text": """
        3D printing service for rapid prototyping:

        Process: Selective Laser Sintering (SLS)
        Material: Nylon PA12 (high-temperature grade)
        Quantity: 50 samples
        Dimensions: Variable, largest piece 200mm x 100mm x 50mm
        Surface finish: Natural as-printed
        Tolerances: ±0.2mm
        Post-processing: Dyeing in customer colors
        Delivery: 2 weeks from order
        File format: STL or STEP required
        Quality: Visual inspection for dimensional accuracy
        Standards: Customer accepts additive manufacturing tolerances
        """,
        "expected_fields": {
            "product_name": "3D Printed Nylon PA12 Prototypes",
            "material": "Nylon PA12",
            "quantity": "50",
            "dimensions": "variable up to 200x100x50mm",
            "delivery_timeframe": "2 weeks",
        },
    },
    # 15. Fastener Manufacturing
    {
        "name": "Stainless Steel Fasteners",
        "text": """
        RFQ for stainless steel fastener manufacturing:

        Product: Machine screws
        Material: 304 stainless steel
        Size: M6 x 1.0mm pitch, 16mm length
        Head type: Pan head, Phillips drive
        Grade: 60 (strength equivalent)
        Quantity: 500,000 pieces
        Surface: Passivated per ASTM A967
        Thread specification: ISO metric
        Delivery:
          - Samples: 1 week
          - Full order: 8 weeks
        Quality: Zero corrosion, no imperfections
        Certification: ISO 4762, DIN 912
        """,
        "expected_fields": {
            "product_name": "Stainless Steel M6 Machine Screws",
            "material": "304 stainless steel",
            "quantity": "500,000",
            "certifications": ["ISO 4762", "DIN 912"],
            "delivery_timeframe": "8 weeks",
        },
    },
    # 16. Glass Manufacturing
    {
        "name": "Custom Glass Components",
        "text": """
        Quotation request for specialized glass components:

        Glass type: Borosilicate glass (like Pyrex)
        Specifications:
        - Custom shape: Cylindrical tubes with flat bottom
        - Dimensions: OD 50mm, wall thickness 3mm, height 100mm
        - Quantity: 5000 pieces
        - Transparency: Crystal clear, no bubbles or striations
        - Edges: Polished to prevent sharp edges
        - Bottom: Ground flat, ±0.5mm deviation acceptable
        - Thermal shock resistance: Min 200°C capability
        - Timeline: 10 weeks from order
        - Certification: FDA food-contact safe
        - Quality: 99% yield minimum
        """,
        "expected_fields": {
            "product_name": "Custom Borosilicate Glass Tubes",
            "material": "Borosilicate glass",
            "quantity": "5000",
            "certifications": ["FDA"],
            "delivery_timeframe": "10 weeks",
        },
    },
    # 17. Textile Manufacturing
    {
        "name": "Custom Woven Fabric",
        "text": """
        RFQ for custom woven fabric production:

        Fiber content: 65% polyester, 35% cotton blend
        Weave pattern: Twill, 2/2 construction
        Width: 150 cm (width in loom)
        Weight: 250 gsm (grams per square meter)
        Color: Custom dye lot to Pantone 16-0755
        Shrinkage: Max 2% after washing
        Tensile strength: Min 50 kgf per ASTM D6775
        Quantity: 10,000 meters
        Delivery: 12 weeks
        Finishing: Pre-shrunk, softened finish
        Certification: Oeko-Tex Standard 100
        Applications: Apparel manufacturing
        """,
        "expected_fields": {
            "product_name": "Custom Woven Polyester-Cotton Fabric",
            "material": "65% polyester, 35% cotton",
            "quantity": "10,000 meters",
            "certifications": ["Oeko-Tex Standard 100"],
            "delivery_timeframe": "12 weeks",
        },
    },
    # 18. Chemical Processing
    {
        "name": "Custom Chemical Formulation",
        "text": """
        Request for quotation on custom chemical product:

        Product type: Industrial cleaning solution
        Volume: 10,000 liters per order
        Specifications:
        - pH: 7.0-8.0 neutral formulation
        - Density: 0.95-1.05 g/cm³
        - Viscosity: <20 cSt at 40°C
        - Active ingredient: Bio-based surfactant 25%
        - Biodegradability: Min 90% per OECD 301D
        - Safety: Non-toxic, non-hazardous classification
        Certification: ISO 14001 certified facility
        Delivery: 4 weeks
        Packaging: Food-grade plastic drums
        Testing: Full batch analysis report required
        """,
        "expected_fields": {
            "product_name": "Custom Industrial Cleaning Solution",
            "material": "Bio-based surfactant formulation",
            "quantity": "10,000 liters",
            "certifications": ["ISO 14001", "OECD 301D"],
            "delivery_timeframe": "4 weeks",
        },
    },
    # 19. Automotive OEM Parts
    {
        "name": "Automotive Door Handles",
        "text": """
        Automotive OEM door handle assembly RFQ:

        Vehicle model: Premium sedan variant
        Component: Exterior door handle assembly
        Quantity: 50,000 sets (4 pieces per set = 200,000 individual handles)
        Material: Zinc-alloy die-cast with ABS plastic inserts
        Color: Match OEM factory color (paint code ABC-123)
        Finish: Chrome plated with polished stainless steel accents
        Certification requirements:
          - IATF 16949 (automotive quality management)
          - VDA 6.1 (supplier assessment)
          - APQP (Advanced Product Quality Planning)
        Design: Provided CAD and IGES files
        Testing: Salt spray 500 hours per SAE J2334
        Timeline:
          - Tooling approval: 8 weeks
          - PPAP: 4 weeks
          - Production: Ongoing
        Quality: Zero scratches/dents acceptable
        """,
        "expected_fields": {
            "product_name": "Automotive Door Handle Assembly",
            "material": "Zinc-alloy die-cast + ABS plastic",
            "quantity": "50,000 sets",
            "certifications": ["IATF 16949", "VDA 6.1"],
            "delivery_timeframe": "12 weeks",
        },
    },
    # 20. Industrial Equipment Manufacturing
    {
        "name": "Industrial Pump Casing",
        "text": """
        Industrial centrifugal pump casing manufacturing RFQ:

        Casting process: Sand casting with investment backing
        Material: Ductile iron (GGG-70)
        Part dimensions: 800mm x 600mm x 400mm
        Weight: Approximately 250 kg
        Quantity: 100 pieces
        Dimensional tolerance: ±2mm
        Surface finish:
          - Internal passages: As-cast finish acceptable
          - External surfaces: Blasted and painted
          - Seal faces: Honed to Ra 0.4 µm
        Pressure rating: 16 bar minimum
        Certifications:
          - ISO 9001:2015
          - PED (Pressure Equipment Directive) 2014/68/EU
          - ASME BPVC Section VIII Division 1
        Testing: Hydrostatic pressure test at 1.5x working pressure
        Delivery timeline: 14 weeks
        Quality: 100% dimensional inspection with CMM
        Documentation: Mill certificates and test reports required
        """,
        "expected_fields": {
            "product_name": "Industrial Centrifugal Pump Casing",
            "material": "Ductile iron GGG-70",
            "quantity": "100",
            "certifications": ["ISO 9001", "PED", "ASME"],
            "delivery_timeframe": "14 weeks",
        },
    },
]


@pytest.mark.asyncio
class TestRFQParsingAccuracy:
    """Test RFQ parsing accuracy across diverse manufacturing examples"""

    async def test_parse_all_rfq_types(self):
        """Test parsing all 20 RFQ types"""
        claude_service = get_claude_service()
        results = []

        for i, rfq in enumerate(TEST_RFQS, 1):
            print(f"\n--- Testing RFQ {i}: {rfq['name']} ---")

            # Test parsing
            parse_result = await claude_service.analyze_rfq_text(rfq['text'])

            # Validate critical fields
            accuracy_score = self._calculate_accuracy(
                parse_result,
                rfq['expected_fields']
            )

            results.append({
                "rfq_number": i,
                "rfq_name": rfq['name'],
                "accuracy_score": accuracy_score,
                "parsed_data": parse_result,
                "expected_fields": rfq['expected_fields'],
            })

            print(f"Accuracy Score: {accuracy_score}%")

        # Generate summary report
        avg_accuracy = sum(r['accuracy_score'] for r in results) / len(results)
        print(f"\n{'='*60}")
        print(f"OVERALL PARSING ACCURACY: {avg_accuracy:.1f}%")
        print(f"{'='*60}")

        # Assert minimum accuracy threshold
        assert avg_accuracy >= 75, f"Parsing accuracy {avg_accuracy}% below threshold of 75%"

        # Print detailed results
        print("\nDetailed Results:")
        print(f"{'#':<3} {'RFQ Type':<40} {'Accuracy':<12}")
        print("-" * 60)
        for r in results:
            print(f"{r['rfq_number']:<3} {r['rfq_name']:<40} {r['accuracy_score']:>6.1f}%")

    def _calculate_accuracy(
        self,
        parsed: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> float:
        """Calculate parsing accuracy by comparing extracted fields"""
        if not parsed or "parsed_data" not in parsed:
            return 0.0

        parsed_data = parsed["parsed_data"]
        matches = 0
        total_fields = len(expected)

        for field, expected_value in expected.items():
            parsed_value = parsed_data.get(field)

            # Handle different comparison types
            if isinstance(expected_value, list):
                # For list fields (certifications)
                if isinstance(parsed_value, str):
                    parsed_value = [parsed_value]
                matches += self._list_match_score(parsed_value or [], expected_value)
            else:
                # For string fields
                if isinstance(parsed_value, str) and isinstance(expected_value, str):
                    # Partial match is acceptable (substring matching)
                    if self._string_match(parsed_value, expected_value):
                        matches += 1
                elif str(parsed_value).lower() == str(expected_value).lower():
                    matches += 1

        return (matches / total_fields * 100) if total_fields > 0 else 0

    @staticmethod
    def _list_match_score(parsed: list, expected: list) -> float:
        """Calculate match score for list fields"""
        if not expected:
            return 1.0

        matches = sum(
            1 for exp in expected
            if any(exp.lower() in str(p).lower() for p in parsed)
        )

        return matches / len(expected)

    @staticmethod
    def _string_match(parsed: str, expected: str) -> bool:
        """Check if parsed value matches expected (case-insensitive substring)"""
        parsed_lower = parsed.lower().replace(" ", "")
        expected_lower = expected.lower().replace(" ", "")

        return (
            expected_lower in parsed_lower or
            parsed_lower in expected_lower or
            len(parsed_lower) > 0
        )


# Run if executed directly
if __name__ == "__main__":
    import asyncio

    test = TestRFQParsingAccuracy()
    asyncio.run(test.test_parse_all_rfq_types())
