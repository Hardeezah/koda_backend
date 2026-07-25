"""
HS Code table seeder.

Usage:
    cd backend
    python -m scripts.seed_hs_codes

Seeds the hs_codes pgvector table with the top-level HS chapters and
representative headings for the categories most relevant to Nigerian trade.
Re-running is idempotent via upsert on the code column.
"""
import asyncio
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

HS_SEED_DATA = [
    {"chapter": "01", "heading": "0101", "code": "010121", "description": "Live horses, pure-bred breeding animals", "notes": "Chapter 01: Live animals"},
    {"chapter": "02", "heading": "0201", "code": "020110", "description": "Fresh or chilled beef carcasses and half-carcasses", "notes": "Chapter 02: Meat and edible offal"},
    {"chapter": "03", "heading": "0302", "code": "030211", "description": "Fresh or chilled trout, salmonidae", "notes": "Chapter 03: Fish"},
    {"chapter": "04", "heading": "0401", "code": "040110", "description": "Milk not concentrated or sweetened, fat content max 1%", "notes": "Chapter 04: Dairy"},
    {"chapter": "07", "heading": "0701", "code": "070110", "description": "Seed potatoes, fresh or chilled", "notes": "Chapter 07: Edible vegetables"},
    {"chapter": "08", "heading": "0801", "code": "080110", "description": "Desiccated coconuts", "notes": "Chapter 08: Edible fruit and nuts"},
    {"chapter": "09", "heading": "0901", "code": "090111", "description": "Coffee, not roasted, not decaffeinated", "notes": "Chapter 09: Coffee, tea, spices"},
    {"chapter": "10", "heading": "1001", "code": "100110", "description": "Durum wheat, seed", "notes": "Chapter 10: Cereals"},
    {"chapter": "11", "heading": "1101", "code": "110100", "description": "Wheat or meslin flour", "notes": "Chapter 11: Milling products"},
    {"chapter": "12", "heading": "1201", "code": "120100", "description": "Soya beans, whether or not broken", "notes": "Chapter 12: Oil seeds"},
    {"chapter": "15", "heading": "1511", "code": "151110", "description": "Palm oil, crude", "notes": "Chapter 15: Animal or vegetable fats"},
    {"chapter": "16", "heading": "1601", "code": "160100", "description": "Sausages and similar products of meat", "notes": "Chapter 16: Preparations of meat"},
    {"chapter": "17", "heading": "1701", "code": "170111", "description": "Cane sugar, raw, in solid form", "notes": "Chapter 17: Sugars"},
    {"chapter": "18", "heading": "1801", "code": "180100", "description": "Cocoa beans, whole or broken, raw or roasted", "notes": "Chapter 18: Cocoa"},
    {"chapter": "19", "heading": "1901", "code": "190110", "description": "Preparations for infant use, retail sale", "notes": "Chapter 19: Preparations of cereals"},
    {"chapter": "20", "heading": "2001", "code": "200110", "description": "Cucumbers and gherkins, prepared or preserved by vinegar", "notes": "Chapter 20: Preparations of vegetables"},
    {"chapter": "21", "heading": "2101", "code": "210111", "description": "Extracts, essences and concentrates of coffee", "notes": "Chapter 21: Miscellaneous edible preparations"},
    {"chapter": "22", "heading": "2201", "code": "220110", "description": "Mineral waters and aerated waters, not sweetened", "notes": "Chapter 22: Beverages"},
    {"chapter": "24", "heading": "2401", "code": "240110", "description": "Tobacco, not stemmed or stripped, flue-cured", "notes": "Chapter 24: Tobacco"},
    {"chapter": "25", "heading": "2505", "code": "250500", "description": "Natural sands of all kinds, not metal-bearing", "notes": "Chapter 25: Salt, sulphur, earths, stone"},
    {"chapter": "27", "heading": "2709", "code": "270900", "description": "Petroleum oils and oils from bituminous minerals, crude", "notes": "Chapter 27: Mineral fuels"},
    {"chapter": "28", "heading": "2801", "code": "280110", "description": "Chlorine", "notes": "Chapter 28: Inorganic chemicals"},
    {"chapter": "29", "heading": "2901", "code": "290110", "description": "Acyclic hydrocarbons, saturated", "notes": "Chapter 29: Organic chemicals"},
    {"chapter": "30", "heading": "3004", "code": "300410", "description": "Medicaments containing penicillins or other antibiotics, retail packs", "notes": "Chapter 30: Pharmaceutical products"},
    {"chapter": "30", "heading": "3003", "code": "300320", "description": "Medicaments containing antibiotics, not retail", "notes": "Chapter 30: Pharmaceutical products"},
    {"chapter": "30", "heading": "3004", "code": "300490", "description": "Medicaments, other, retail packs", "notes": "Chapter 30: Pharmaceutical products - general"},
    {"chapter": "30", "heading": "3004", "code": "300450", "description": "Medicaments containing vitamins or other nutritional products", "notes": "Chapter 30: Vitamins and supplements"},
    {"chapter": "33", "heading": "3301", "code": "330110", "description": "Essential oils of bergamot, not deterpenated", "notes": "Chapter 33: Essential oils, perfumery"},
    {"chapter": "33", "heading": "3304", "code": "330410", "description": "Lip make-up preparations", "notes": "Chapter 33: Cosmetics, skin care"},
    {"chapter": "33", "heading": "3305", "code": "330510", "description": "Shampoos", "notes": "Chapter 33: Hair care products"},
    {"chapter": "34", "heading": "3401", "code": "340111", "description": "Soap and organic surface-active products, in bars, for toilet use", "notes": "Chapter 34: Soap, waxes, candles"},
    {"chapter": "38", "heading": "3808", "code": "380810", "description": "Insecticides, retail packaging", "notes": "Chapter 38: Miscellaneous chemical products"},
    {"chapter": "39", "heading": "3901", "code": "390110", "description": "Polyethylene, specific gravity less than 0.94, primary forms", "notes": "Chapter 39: Plastics"},
    {"chapter": "40", "heading": "4011", "code": "401110", "description": "New pneumatic tyres, of rubber, for motor cars", "notes": "Chapter 40: Rubber and articles"},
    {"chapter": "44", "heading": "4407", "code": "440710", "description": "Wood sawn or chipped lengthwise, coniferous", "notes": "Chapter 44: Wood and articles of wood"},
    {"chapter": "48", "heading": "4802", "code": "480210", "description": "Hand-made paper and paperboard", "notes": "Chapter 48: Paper and paperboard"},
    {"chapter": "50", "heading": "5007", "code": "500710", "description": "Woven fabrics of silk or silk waste, containing 85% or more by weight of silk", "notes": "Chapter 50: Silk"},
    {"chapter": "52", "heading": "5208", "code": "520811", "description": "Woven fabrics of cotton, plain weave, not more than 100g/m2, bleached", "notes": "Chapter 52: Cotton fabrics"},
    {"chapter": "54", "heading": "5407", "code": "540710", "description": "Woven fabrics of high tenacity yarn of nylon", "notes": "Chapter 54: Man-made filaments"},
    {"chapter": "61", "heading": "6101", "code": "610110", "description": "Men overcoats of wool or fine animal hair, knitted", "notes": "Chapter 61: Knitted or crocheted clothing"},
    {"chapter": "62", "heading": "6201", "code": "620111", "description": "Men overcoats of wool, not knitted", "notes": "Chapter 62: Not knitted or crocheted clothing"},
    {"chapter": "64", "heading": "6401", "code": "640112", "description": "Waterproof footwear with outer soles and uppers of rubber or plastics, covering the ankle", "notes": "Chapter 64: Footwear"},
    {"chapter": "68", "heading": "6810", "code": "681011", "description": "Building blocks and bricks of cement, concrete or artificial stone", "notes": "Chapter 68: Building materials, stone"},
    {"chapter": "69", "heading": "6907", "code": "690710", "description": "Unglazed ceramic flags and paving, hearth or wall tiles", "notes": "Chapter 69: Ceramic products, tiles"},
    {"chapter": "70", "heading": "7003", "code": "700310", "description": "Cast glass and rolled glass, non-wired sheets, coloured throughout", "notes": "Chapter 70: Glass"},
    {"chapter": "72", "heading": "7207", "code": "720711", "description": "Semi-finished products of iron or non-alloy steel, less than 0.25% carbon, rectangular cross-section", "notes": "Chapter 72: Iron and steel"},
    {"chapter": "73", "heading": "7308", "code": "730811", "description": "Bridges and bridge-sections of iron or steel", "notes": "Chapter 73: Articles of iron or steel"},
    {"chapter": "74", "heading": "7401", "code": "740100", "description": "Copper mattes; cement copper", "notes": "Chapter 74: Copper"},
    {"chapter": "84", "heading": "8415", "code": "841510", "description": "Air conditioning machines, window or wall types, self-contained", "notes": "Chapter 84: Machinery, mechanical appliances"},
    {"chapter": "84", "heading": "8471", "code": "847130", "description": "Portable digital automatic data processing machines, weighing not more than 10 kg", "notes": "Chapter 84: Laptops and portable computers"},
    {"chapter": "84", "heading": "8472", "code": "847210", "description": "Duplicating machines", "notes": "Chapter 84: Office machinery"},
    {"chapter": "84", "heading": "8418", "code": "841810", "description": "Combined refrigerator-freezers with separate external doors", "notes": "Chapter 84: Refrigerators and freezers"},
    {"chapter": "85", "heading": "8517", "code": "851712", "description": "Telephones for cellular networks, smartphones", "notes": "Chapter 85: Mobile phones and smartphones"},
    {"chapter": "85", "heading": "8525", "code": "852520", "description": "Transmission apparatus for radio-telephony incorporating reception apparatus, television cameras", "notes": "Chapter 85: Electrical machinery"},
    {"chapter": "85", "heading": "8544", "code": "854411", "description": "Winding wire of copper for electrical purposes", "notes": "Chapter 85: Electrical wires and cables"},
    {"chapter": "87", "heading": "8703", "code": "870321", "description": "Passenger motor vehicles with spark-ignition engine, cylinder capacity not exceeding 1000cc", "notes": "Chapter 87: Vehicles, passenger cars"},
    {"chapter": "87", "heading": "8704", "code": "870410", "description": "Dumpers for off-highway use", "notes": "Chapter 87: Motor vehicles for transport of goods"},
    {"chapter": "88", "heading": "8802", "code": "880211", "description": "Helicopters of an unladen weight not exceeding 2000kg", "notes": "Chapter 88: Aircraft"},
    {"chapter": "89", "heading": "8901", "code": "890110", "description": "Cruise ships, excursion boats and similar vessels", "notes": "Chapter 89: Ships and boats"},
    {"chapter": "90", "heading": "9018", "code": "901811", "description": "Electro-cardiographs", "notes": "Chapter 90: Medical instruments"},
    {"chapter": "90", "heading": "9027", "code": "902710", "description": "Gas or smoke analysis apparatus", "notes": "Chapter 90: Optical, measuring instruments"},
    {"chapter": "94", "heading": "9401", "code": "940110", "description": "Seats for aircraft", "notes": "Chapter 94: Furniture"},
    {"chapter": "94", "heading": "9403", "code": "940310", "description": "Metal furniture for offices", "notes": "Chapter 94: Office furniture"},
    {"chapter": "95", "heading": "9503", "code": "950300", "description": "Tricycles, scooters, pedal cars and similar wheeled toys; dolls carriages; dolls", "notes": "Chapter 95: Toys and games"},
]


async def main():
    from app.infrastructure.db.hs_code_repository import hs_code_repository

    print(f"Seeding {len(HS_SEED_DATA)} HS code entries...")
    await hs_code_repository.upsert(HS_SEED_DATA)
    print("HS code seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
